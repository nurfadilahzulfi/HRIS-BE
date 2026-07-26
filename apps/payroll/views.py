from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardResultsPagination
from .models import SalaryComponent, EmployeeSalaryComponent, OvertimeRecord, PayrollPeriod, PayrollItem
from .serializers import (
    SalaryComponentSerializer, EmployeeSalaryComponentSerializer,
    OvertimeRecordSerializer, PayrollPeriodSerializer, PayrollItemSerializer,
)
from .calculator import calculate_payroll_item


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['payroll'])
class SalaryComponentViewSet(viewsets.ModelViewSet):
    serializer_class   = SalaryComponentSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter]
    filterset_fields   = ['entity', 'component_type', 'is_active']
    search_fields      = ['name']

    def get_queryset(self):
        user = self.request.user
        qs = SalaryComponent.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['payroll'])
class EmployeeSalaryComponentViewSet(viewsets.ModelViewSet):
    serializer_class   = EmployeeSalaryComponentSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['employee', 'component', 'is_active']

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeSalaryComponent.objects.select_related('employee', 'component').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs


@extend_schema(tags=['payroll'])
class OvertimeRecordViewSet(viewsets.ModelViewSet):
    serializer_class   = OvertimeRecordSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['employee', 'overtime_type', 'payroll_period']
    search_fields      = ['employee__full_name', 'employee__employee_id']
    ordering_fields    = ['date', 'hours_worked']
    ordering           = ['-date']

    def get_queryset(self):
        user = self.request.user
        qs = OvertimeRecord.objects.select_related('employee', 'payroll_period').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs

    @extend_schema(summary='Bulk import overtime records')
    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        records = request.data if isinstance(request.data, list) else request.data.get('records', [])
        serializer = OvertimeRecordSerializer(data=records, many=True)
        serializer.is_valid(raise_exception=True)
        created = OvertimeRecord.objects.bulk_create([
            OvertimeRecord(**item) for item in serializer.validated_data
        ])
        return Response({
            'success': True,
            'created': len(created),
            'message': f'{len(created)} record lembur berhasil diimport.',
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['payroll'])
class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class   = PayrollPeriodSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_fields   = ['entity', 'month', 'year', 'status']
    ordering_fields    = ['year', 'month']
    ordering           = ['-year', '-month']

    def get_queryset(self):
        user = self.request.user
        qs = PayrollPeriod.objects.select_related('entity', 'created_by').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(summary='Calculate payroll for all employees in this period')
    @action(detail=True, methods=['post'], url_path='calculate')
    def calculate(self, request, pk=None):
        period = self.get_object()
        if period.status == PayrollPeriod.Status.FINALIZED:
            return Response({'success': False, 'message': 'Periode sudah difinalisasi.'}, status=400)

        period.status = PayrollPeriod.Status.PROCESSING
        period.save(update_fields=['status'])

        # Get all active employees in this entity
        from apps.employees.models import Employee
        employees = Employee.objects.filter(entity=period.entity, status='ACTIVE')
        calculated = 0
        errors = []

        for emp in employees:
            try:
                calculate_payroll_item(period, emp)
                calculated += 1
            except Exception as e:
                errors.append({'employee': emp.full_name, 'error': str(e)})

        period.status = PayrollPeriod.Status.DRAFT
        period.save(update_fields=['status'])

        return Response({
            'success': True,
            'calculated': calculated,
            'errors': errors,
            'message': f'Kalkulasi selesai: {calculated} karyawan diproses.',
        })

    @extend_schema(summary='Finalize payroll period — cannot be undone')
    @action(detail=True, methods=['post'], url_path='finalize')
    def finalize(self, request, pk=None):
        period = self.get_object()
        if period.status == PayrollPeriod.Status.FINALIZED:
            return Response({'success': False, 'message': 'Periode sudah difinalisasi.'}, status=400)
        if not period.items.exists():
            return Response({'success': False, 'message': 'Belum ada item payroll. Jalankan kalkulasi terlebih dahulu.'}, status=400)

        period.status       = PayrollPeriod.Status.FINALIZED
        period.finalized_at = timezone.now()
        period.save(update_fields=['status', 'finalized_at'])

        # Trigger PDF generation via Celery
        try:
            from apps.salary_slip.tasks import generate_salary_slips_for_period
            generate_salary_slips_for_period.delay(period.id)
        except Exception:
            pass  # Celery may not be available in all envs

        return Response({'success': True, 'message': 'Periode payroll berhasil difinalisasi. Slip gaji sedang digenerate.'})

    @extend_schema(summary='Get all payroll items for this period')
    @action(detail=True, methods=['get'], url_path='items')
    def items(self, request, pk=None):
        period = self.get_object()
        qs = period.items.select_related('employee').all()
        page = self.paginate_queryset(qs)
        serializer = PayrollItemSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
