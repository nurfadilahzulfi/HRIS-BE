from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.pagination import StandardResultsPagination
from .models import Department, Position, Employee
from .serializers import (
    DepartmentSerializer,
    PositionSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    OrgChartSerializer,
)


class IsHROrReadOnly(permissions.BasePermission):
    """HR and above can write; authenticated users can read."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['departments'])
class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class   = DepartmentSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['entity', 'is_active']
    search_fields      = ['name', 'code']
    ordering_fields    = ['name', 'created_at']
    ordering           = ['name']

    def get_queryset(self):
        user = self.request.user
        qs   = Department.objects.select_related('entity', 'head').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['positions'])
class PositionViewSet(viewsets.ModelViewSet):
    serializer_class   = PositionSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['department', 'is_active']
    search_fields      = ['name']
    ordering_fields    = ['name', 'grade_level']
    ordering           = ['-grade_level', 'name']

    def get_queryset(self):
        user = self.request.user
        qs   = Position.objects.select_related('department__entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(department__entity=user.entity)
        return qs


@extend_schema(tags=['employees'])
class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['entity', 'department', 'position', 'status', 'gender', 'ptkp_status']
    search_fields      = ['full_name', 'employee_id', 'nik', 'phone']
    ordering_fields    = ['full_name', 'employee_id', 'join_date', 'created_at']
    ordering           = ['full_name']

    def get_queryset(self):
        user = self.request.user
        qs   = Employee.objects.select_related(
            'entity', 'department', 'position', 'manager'
        ).all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    @extend_schema(
        summary='Get employee org chart',
        description='Returns hierarchical org chart tree starting from the given employee.',
    )
    @action(detail=True, methods=['get'], url_path='org-chart')
    def org_chart(self, request, pk=None):
        employee = self.get_object()
        serializer = OrgChartSerializer(employee, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    @extend_schema(summary='Get direct subordinates of an employee')
    @action(detail=True, methods=['get'], url_path='subordinates')
    def subordinates(self, request, pk=None):
        employee = self.get_object()
        subs = employee.subordinates.filter(status='ACTIVE').select_related(
            'department', 'position'
        )
        serializer = EmployeeListSerializer(subs, many=True, context={'request': request})
        return Response({
            'success': True,
            'count': subs.count(),
            'data': serializer.data,
        })

    @extend_schema(summary='Terminate an employee')
    @action(detail=True, methods=['post'], url_path='terminate')
    def terminate(self, request, pk=None):
        employee = self.get_object()
        if not request.user.is_hr:
            return Response({'success': False, 'message': 'Tidak memiliki akses.'}, status=403)
        employee.status = Employee.Status.TERMINATED
        from django.utils import timezone
        employee.resign_date = timezone.now().date()
        employee.save(update_fields=['status', 'resign_date'])
        return Response({'success': True, 'message': f'{employee.full_name} telah di-terminate.'})
