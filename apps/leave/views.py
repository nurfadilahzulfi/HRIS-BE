from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.core.pagination import StandardResultsPagination
from .models import LeaveType, LeaveBalance, LeaveRequest, LeaveApproval
from .serializers import (
    LeaveTypeSerializer,
    LeaveBalanceSerializer,
    LeaveRequestSerializer,
    LeaveRequestListSerializer,
    ApproveRejectSerializer,
)


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['leave'])
class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class   = LeaveTypeSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter]
    filterset_fields   = ['entity', 'applicable_to', 'is_active']
    search_fields      = ['name']

    def get_queryset(self):
        user = self.request.user
        qs = LeaveType.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['leave'])
class LeaveBalanceViewSet(viewsets.ModelViewSet):
    serializer_class   = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = StandardResultsPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_fields   = ['employee', 'leave_type', 'year']

    def get_queryset(self):
        user = self.request.user
        qs = LeaveBalance.objects.select_related('employee', 'leave_type').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(employee__entity=user.entity)
        return qs

    @extend_schema(summary="Get current user's leave balances")
    @action(detail=False, methods=['get'], url_path='me')
    def my_balances(self, request):
        if not hasattr(request.user, 'employee') or not request.user.employee:
            return Response({'success': False, 'message': 'User tidak terhubung ke profil karyawan.'}, status=400)
        year = request.query_params.get('year', timezone.now().year)
        balances = LeaveBalance.objects.filter(employee=request.user.employee, year=year)
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response({'success': True, 'data': serializer.data})


@extend_schema(tags=['leave'])
class LeaveRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = StandardResultsPagination
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['status', 'leave_type', 'employee']
    search_fields      = ['employee__full_name']
    ordering_fields    = ['created_at', 'start_date']
    ordering           = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequest.objects.select_related(
            'employee', 'leave_type'
        ).prefetch_related('approvals__approver').all()
        # Employee can only see own requests
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            return qs.filter(employee__entity=user.entity)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return LeaveRequestListSerializer
        return LeaveRequestSerializer

    @extend_schema(summary='Submit a leave request for approval')
    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        leave_req = self.get_object()
        if leave_req.status != LeaveRequest.Status.DRAFT:
            return Response({'success': False, 'message': 'Hanya permohonan berstatus Draft yang bisa diajukan.'}, status=400)

        leave_req.status       = LeaveRequest.Status.PENDING
        leave_req.submitted_at = timezone.now()
        leave_req.save(update_fields=['status', 'submitted_at'])

        # Create approval records based on entity leave_levels
        employee = leave_req.employee
        entity   = employee.entity
        levels   = entity.leave_approval_levels
        manager  = employee.manager

        for level in range(1, levels + 1):
            if manager:
                LeaveApproval.objects.get_or_create(
                    leave_request=leave_req,
                    level=level,
                    defaults={'approver': manager, 'status': LeaveApproval.Status.PENDING},
                )
                manager = manager.manager  # go up the chain
            else:
                break

        return Response({'success': True, 'message': 'Permohonan cuti berhasil diajukan.'})

    @extend_schema(summary='Approve a leave request', request=ApproveRejectSerializer)
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        leave_req = self.get_object()
        user_emp  = getattr(request.user, 'employee', None)
        if not user_emp:
            return Response({'success': False, 'message': 'User tidak terhubung ke profil karyawan.'}, status=400)

        approval = LeaveApproval.objects.filter(
            leave_request=leave_req, approver=user_emp, status=LeaveApproval.Status.PENDING
        ).first()
        if not approval:
            return Response({'success': False, 'message': 'Tidak ada permohonan yang perlu disetujui.'}, status=400)

        notes = request.data.get('notes', '')
        approval.status   = LeaveApproval.Status.APPROVED
        approval.notes    = notes
        approval.acted_at = timezone.now()
        approval.save()

        # Check if all approvals done
        pending = LeaveApproval.objects.filter(leave_request=leave_req, status=LeaveApproval.Status.PENDING)
        if not pending.exists():
            leave_req.status = LeaveRequest.Status.APPROVED
            leave_req.save(update_fields=['status'])
            # Update leave balance
            try:
                balance = LeaveBalance.objects.get(
                    employee=leave_req.employee,
                    leave_type=leave_req.leave_type,
                    year=leave_req.start_date.year,
                )
                balance.used += int(leave_req.total_days)
                balance.save(update_fields=['used'])
            except LeaveBalance.DoesNotExist:
                pass

        return Response({'success': True, 'message': 'Cuti berhasil disetujui.'})

    @extend_schema(summary='Reject a leave request', request=ApproveRejectSerializer)
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        leave_req = self.get_object()
        user_emp  = getattr(request.user, 'employee', None)
        if not user_emp:
            return Response({'success': False, 'message': 'User tidak terhubung ke profil karyawan.'}, status=400)

        approval = LeaveApproval.objects.filter(
            leave_request=leave_req, approver=user_emp, status=LeaveApproval.Status.PENDING
        ).first()
        if not approval:
            return Response({'success': False, 'message': 'Tidak ada permohonan yang perlu ditolak.'}, status=400)

        notes = request.data.get('notes', '')
        approval.status   = LeaveApproval.Status.REJECTED
        approval.notes    = notes
        approval.acted_at = timezone.now()
        approval.save()

        leave_req.status = LeaveRequest.Status.REJECTED
        leave_req.save(update_fields=['status'])

        return Response({'success': True, 'message': 'Cuti berhasil ditolak.'})

    @extend_schema(summary='Get leave requests pending your approval')
    @action(detail=False, methods=['get'], url_path='pending-my-approval')
    def pending_my_approval(self, request):
        user_emp = getattr(request.user, 'employee', None)
        if not user_emp:
            return Response({'data': []})
        pending_ids = LeaveApproval.objects.filter(
            approver=user_emp, status=LeaveApproval.Status.PENDING
        ).values_list('leave_request_id', flat=True)
        qs = LeaveRequest.objects.filter(id__in=pending_ids).select_related('employee', 'leave_type')
        serializer = LeaveRequestListSerializer(qs, many=True)
        return Response({'success': True, 'count': qs.count(), 'data': serializer.data})

    @extend_schema(
        summary='Get leave calendar events',
        parameters=[
            OpenApiParameter('month', int, description='Month (1-12)'),
            OpenApiParameter('year', int, description='Year (e.g. 2024)')
        ]
    )
    @action(detail=False, methods=['get'], url_path='calendar')
    def calendar(self, request):
        now = timezone.now()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))

        qs = self.get_queryset().filter(
            start_date__year=year,
            start_date__month=month
        ).select_related('employee', 'leave_type')

        events = []
        for req in qs:
            events.append({
                'id': req.id,
                'employee_id': req.employee.id,
                'employee_name': req.employee.full_name,
                'leave_type': req.leave_type.name,
                'start_date': str(req.start_date),
                'end_date': str(req.end_date),
                'total_days': float(req.total_days),
                'status': req.status
            })

        return Response({
            'success': True,
            'month': month,
            'year': year,
            'count': len(events),
            'data': events
        })
