from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.permissions import IsHROrReadOnly
from apps.core.pagination import StandardResultsPagination
from .models import Contract, ContractRenewal
from .serializers import (
    ContractSerializer,
    ContractListSerializer,
    ContractRenewalSerializer,
    RenewContractSerializer,
)


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
        old_contract = self.get_object()
        serializer = RenewContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # Mark old contract as RENEWED
            old_contract.status = Contract.Status.RENEWED
            old_contract.save(update_fields=['status'])

            # Create new ACTIVE contract for employee
            new_salary = data.get('new_salary_base') or old_contract.salary_base
            new_contract = Contract.objects.create(
                employee=old_contract.employee,
                contract_type=old_contract.contract_type,
                start_date=old_contract.end_date,
                end_date=data['new_end_date'],
                salary_base=new_salary,
                status=Contract.Status.ACTIVE,
            )

            # Create renewal audit record linked to original contract
            renewal = ContractRenewal.objects.create(
                original_contract=old_contract,
                new_end_date=data['new_end_date'],
                new_salary_base=new_salary,
                document=data.get('document'),
                notes=data.get('notes', ''),
                renewed_by=request.user,
            )

        return Response({
            'success': True,
            'message': 'Kontrak berhasil diperbarui dengan membuat kontrak aktif baru.',
            'new_contract_id': new_contract.id,
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
