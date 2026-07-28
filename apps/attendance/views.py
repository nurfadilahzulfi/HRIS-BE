from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.pagination import StandardResultsPagination
from apps.employees.models import Employee
from .models import WorkSchedule, EmployeeSchedule, AttendanceLog
from .serializers import (
    WorkScheduleSerializer,
    EmployeeScheduleSerializer,
    AttendanceLogSerializer,
    AttendanceSyncSerializer,
)


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['attendance'])
class WorkScheduleViewSet(viewsets.ModelViewSet):
    serializer_class   = WorkScheduleSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['entity', 'is_active']
    search_fields      = ['name']

    def get_queryset(self):
        user = self.request.user
        qs = WorkSchedule.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['attendance'])
class EmployeeScheduleViewSet(viewsets.ModelViewSet):
    serializer_class   = EmployeeScheduleSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['employee', 'schedule']

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeSchedule.objects.select_related('employee', 'schedule').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs


@extend_schema(tags=['attendance'])
class AttendanceLogViewSet(viewsets.ModelViewSet):
    serializer_class   = AttendanceLogSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['employee', 'date', 'source']
    search_fields      = ['employee__full_name', 'employee__employee_id']
    ordering_fields    = ['date', 'check_in']
    ordering           = ['-date']

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceLog.objects.select_related('employee').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs

    @extend_schema(
        summary='Sync attendance from finger machine / middleware',
        request=AttendanceSyncSerializer,
    )
    @action(detail=False, methods=['post'], url_path='sync', permission_classes=[permissions.IsAuthenticated])
    def sync(self, request):
        """
        API-agnostic endpoint: accepts attendance data from any finger machine
        middleware or external system via POST.
        """
        serializer = AttendanceSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        emp_id = data['employee_id']
        try:
            employee = Employee.objects.get(employee_id=emp_id)
        except Employee.DoesNotExist:
            try:
                employee = Employee.objects.get(nik=emp_id)
            except Employee.DoesNotExist:
                return Response(
                    {'success': False, 'message': f'Karyawan dengan ID/NIK "{emp_id}" tidak ditemukan.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        log, created = AttendanceLog.objects.update_or_create(
            employee=employee,
            date=data['date'],
            defaults={
                'check_in':  data.get('check_in'),
                'check_out': data.get('check_out'),
                'source':    data.get('source', 'FINGER'),
                'notes':     data.get('notes', ''),
                'raw_data':  data.get('raw_data'),
            },
        )

        return Response({
            'success': True,
            'created': created,
            'message': 'Absensi berhasil disinkronkan.',
            'data': AttendanceLogSerializer(log).data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @extend_schema(
        summary='Bulk import attendance from JSON list (CSV/finger export)',
        description=(
            'Import multiple attendance records at once. '
            'Accepts a JSON array with keys: employee_id, date, check_in, '
            'check_out, source, notes, raw_data. '
            'employee_id may be the Employee ID string (e.g. HO-2024-0001) or NIK.'
        ),
    )
    @action(detail=False, methods=['post'], url_path='import', permission_classes=[permissions.IsAuthenticated])
    def bulk_import(self, request):
        """POST /api/attendance/logs/import/ — bulk upsert attendance records."""
        records = request.data if isinstance(request.data, list) else request.data.get('records', [])

        if not records:
            return Response({'success': False, 'message': 'Tidak ada data untuk diimport.'}, status=400)

        imported, skipped, errors = 0, 0, []

        for idx, rec in enumerate(records):
            ser = AttendanceSyncSerializer(data=rec)
            if not ser.is_valid():
                errors.append({'index': idx, 'errors': ser.errors})
                skipped += 1
                continue

            data = ser.validated_data
            emp_id = data['employee_id']

            employee = None
            for lookup in [{'employee_id': emp_id}, {'nik': emp_id}]:
                try:
                    employee = Employee.objects.get(**lookup)
                    break
                except Employee.DoesNotExist:
                    continue

            if not employee:
                errors.append({'index': idx, 'employee_id': emp_id, 'error': 'Karyawan tidak ditemukan'})
                skipped += 1
                continue

            try:
                AttendanceLog.objects.update_or_create(
                    employee=employee,
                    date=data['date'],
                    defaults={
                        'check_in':  data.get('check_in'),
                        'check_out': data.get('check_out'),
                        'source':    data.get('source', 'MANUAL'),
                        'notes':     data.get('notes', ''),
                        'raw_data':  data.get('raw_data'),
                    },
                )
                imported += 1
            except Exception as e:
                errors.append({'index': idx, 'employee_id': emp_id, 'error': str(e)})
                skipped += 1

        return Response({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'message': f'Import selesai: {imported} record berhasil, {skipped} dilewati.',
        })

    @extend_schema(
        summary='Get attendance summary for a month',
        parameters=[
            OpenApiParameter('month', int, description='Month (1–12)'),
            OpenApiParameter('year',  int, description='Year (e.g. 2024)'),
            OpenApiParameter('employee_id', int, description='Filter by employee DB id'),
        ],
    )
    @action(detail=False, methods=['get'], url_path=r'summary/(?P<month>\d+)/(?P<year>\d+)')
    def summary(self, request, month, year):
        qs = self.get_queryset().filter(date__month=month, date__year=year)
        emp_id = request.query_params.get('employee_id')
        if emp_id:
            qs = qs.filter(employee_id=emp_id)

        total_days     = qs.count()
        late_days      = qs.filter(late_minutes__gt=0).count()
        total_late_min = sum(a.late_minutes for a in qs)

        return Response({
            'success': True,
            'month': int(month),
            'year': int(year),
            'total_records': total_days,
            'late_days': late_days,
            'total_late_minutes': total_late_min,
        })
