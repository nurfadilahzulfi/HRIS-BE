from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.pagination import StandardResultsPagination
from .models import Contract, ContractRenewal
from .serializers import (
    ContractSerializer,
    ContractListSerializer,
    ContractRenewalSerializer,
    RenewContractSerializer,
)


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['contracts'])
class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['contract_type', 'status', 'employee__entity']
    search_fields      = ['employee__full_name', 'employee__employee_id']
    ordering_fields    = ['start_date', 'end_date', 'created_at']
    ordering           = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        qs   = Contract.objects.select_related(
            'employee__entity', 'employee__department'
        ).prefetch_related('renewals').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        return ContractSerializer

    @extend_schema(
        summary='Renew a contract',
        request=RenewContractSerializer,
    )
    @action(detail=True, methods=['post'], url_path='renew', parser_classes=[MultiPartParser, FormParser, JSONParser])
    def renew(self, request, pk=None):
        contract = self.get_object()
        serializer = RenewContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Create renewal record
        renewal = ContractRenewal.objects.create(
            original_contract=contract,
            new_end_date=data['new_end_date'],
            new_salary_base=data.get('new_salary_base'),
            document=data.get('document'),
            notes=data.get('notes', ''),
            renewed_by=request.user,
        )

        # Update original contract
        contract.end_date = data['new_end_date']
        if data.get('new_salary_base'):
            contract.salary_base = data['new_salary_base']
        contract.status = Contract.Status.RENEWED
        contract.save(update_fields=['end_date', 'salary_base', 'status'])

        return Response({
            'success': True,
            'message': 'Kontrak berhasil diperbarui.',
            'renewal': ContractRenewalSerializer(renewal).data,
        })

    @extend_schema(
        summary='Get contracts expiring soon',
        parameters=[
            OpenApiParameter('days', int, description='Number of days threshold (default: 30)'),
        ],
    )
    @action(detail=False, methods=['get'], url_path='expiring-soon')
    def expiring_soon(self, request):
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        threshold = today + timezone.timedelta(days=days)

        qs = self.get_queryset().filter(
            status=Contract.Status.ACTIVE,
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=threshold,
        ).order_by('end_date')

        serializer = ContractListSerializer(qs, many=True, context={'request': request})
        return Response({
            'success': True,
            'count': qs.count(),
            'days_threshold': days,
            'data': serializer.data,
        })
