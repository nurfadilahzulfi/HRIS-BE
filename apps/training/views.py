from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.pagination import StandardResultsPagination
from apps.employees.models import Employee
from .models import TrainingCategory, TrainingProgram, TrainingParticipant
from .serializers import TrainingCategorySerializer, TrainingProgramSerializer, TrainingParticipantSerializer


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


def _build_kpi_snapshot_helper(employee):
    """Ambil snapshot KPI aktif karyawan terkini."""
    from apps.kpi.models import EmployeeKPIAssignment
    latest_kpi = (
        EmployeeKPIAssignment.objects
        .filter(employee=employee)
        .order_by('-period_year', '-period_index')
        .first()
    )
    if not latest_kpi:
        return None

    results = []
    for r in latest_kpi.results.select_related('kpi_item').all():
        results.append({
            'indicator': r.kpi_item.indicator,
            'target': float(r.kpi_item.target),
            'unit': r.kpi_item.unit,
            'weight': float(r.kpi_item.weight),
            'actual_achievement': float(r.actual_achievement),
            'score': float(r.score),
        })

    return {
        'assignment_id': latest_kpi.id,
        'template_title': latest_kpi.template.title if latest_kpi.template else '',
        'period_year': latest_kpi.period_year,
        'period_index': latest_kpi.period_index,
        'status': latest_kpi.status,
        'final_score': float(latest_kpi.final_score) if latest_kpi.final_score is not None else None,
        'indicators': results,
    }


@extend_schema(tags=['training-category'])
class TrainingCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingCategorySerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['entity']
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        qs = TrainingCategory.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['training'])
class TrainingProgramViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingProgramSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entity', 'category', 'status', 'is_active']
    search_fields = ['title', 'trainer', 'location']
    ordering_fields = ['start_date', 'title']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        qs = TrainingProgram.objects.select_related('entity', 'category').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs

    @extend_schema(
        summary='Register an employee to this training program',
        description='Registers logged-in employee or target employee to training program with KPI snapshot.',
    )
    @action(detail=True, methods=['post'], url_path='register', permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        program = self.get_object()
        emp_id = request.data.get('employee_id')

        if emp_id:
            try:
                employee = Employee.objects.get(id=emp_id)
            except Employee.DoesNotExist:
                return Response({'success': False, 'message': 'Karyawan tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            employee = getattr(request.user, 'employee', None)
            if not employee:
                return Response({'success': False, 'message': 'Akun Anda tidak terhubung dengan data Karyawan.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check max participants
        if program.max_participants and program.participants.count() >= program.max_participants:
            return Response({'success': False, 'message': 'Kuota pelatihan sudah penuh.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing registration
        participant, created = TrainingParticipant.objects.get_or_create(
            program=program,
            employee=employee,
            defaults={
                'status': 'REGISTERED',
                'kpi_snapshot': _build_kpi_snapshot_helper(employee)
            }
        )

        if not created:
            return Response({'success': False, 'message': 'Karyawan sudah terdaftar dalam pelatihan ini.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': 'Berhasil mendaftar pelatihan.',
            'data': TrainingParticipantSerializer(participant).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['training-participant'])
class TrainingParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingParticipantSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['program', 'employee', 'status', 'attendance']
    search_fields = ['employee__full_name']

    def get_queryset(self):
        user = self.request.user
        qs = TrainingParticipant.objects.select_related('program', 'employee').all()
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(program__entity=user.entity)
        return qs

    def perform_create(self, serializer):
        employee = serializer.validated_data.get('employee')
        kpi_data = _build_kpi_snapshot_helper(employee)
        serializer.save(kpi_snapshot=kpi_data)

    @extend_schema(summary='Get my training history')
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def my_trainings(self, request):
        user_emp = getattr(request.user, 'employee', None)
        if not user_emp:
            return Response({'success': True, 'count': 0, 'data': []})

        qs = TrainingParticipant.objects.filter(employee=user_emp).select_related('program', 'program__category')
        serializer = TrainingParticipantSerializer(qs, many=True)
        return Response({'success': True, 'count': qs.count(), 'data': serializer.data})
