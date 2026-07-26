from django.http import FileResponse
from django.core.mail import EmailMessage
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardResultsPagination
from .models import SignatureConfig, SalarySlip
from .serializers import SignatureConfigSerializer, SalarySlipSerializer
from .generator import generate_slip_pdf


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['salary-slip'])
class SignatureConfigViewSet(viewsets.ModelViewSet):
    serializer_class   = SignatureConfigSerializer
    permission_classes = [IsHROrReadOnly]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        qs = SignatureConfig.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['salary-slip'])
class SalarySlipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = SalarySlipSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = StandardResultsPagination
    filterset_fields   = ['is_sent', 'is_signed']

    def get_queryset(self):
        user = self.request.user
        qs = SalarySlip.objects.select_related(
            'payroll_item__employee', 'payroll_item__period'
        ).all()
        # Employee can only see own slips
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(payroll_item__employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            return qs.filter(payroll_item__period__entity=user.entity)
        return qs

    @extend_schema(summary="Get current user's salary slips")
    @action(detail=False, methods=['get'], url_path='me')
    def my_slips(self, request):
        if not request.user.employee:
            return Response({'data': []})
        slips = SalarySlip.objects.filter(
            payroll_item__employee=request.user.employee
        ).order_by('-created_at')
        serializer = SalarySlipSerializer(slips, many=True, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    @extend_schema(summary='Download PDF salary slip')
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        slip = self.get_object()
        if not slip.pdf_file:
            return Response({'success': False, 'message': 'PDF belum tersedia.'}, status=404)
        response = FileResponse(
            slip.pdf_file.open('rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{slip.slip_number}.pdf"'
        return response

    @extend_schema(summary='Send salary slip via email')
    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        slip = self.get_object()
        emp  = slip.payroll_item.employee
        user = getattr(emp, 'user_account', None)

        if not user or not user.email:
            return Response({'success': False, 'message': 'Karyawan tidak memiliki email.'}, status=400)
        if not slip.pdf_file:
            return Response({'success': False, 'message': 'PDF belum tersedia.'}, status=400)

        period = slip.payroll_item.period
        try:
            msg = EmailMessage(
                subject=f'Slip Gaji {period.month:02d}/{period.year} — {emp.full_name}',
                body=f'Yth. {emp.full_name},\n\nBerikut terlampir slip gaji Anda.\n\nSalam,\nHR Department',
                to=[user.email],
            )
            msg.attach(f'{slip.slip_number}.pdf', slip.pdf_file.read(), 'application/pdf')
            msg.send()

            slip.is_sent = True
            slip.sent_at = timezone.now()
            slip.save(update_fields=['is_sent', 'sent_at'])

            return Response({'success': True, 'message': f'Slip gaji berhasil dikirim ke {user.email}.'})
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=500)


@extend_schema(tags=['salary-slip'])
class PayrollGenerateSlipsView(viewsets.ViewSet):
    """POST /api/payroll/periods/{id}/generate-slips/ — generate all slips for a period."""
    permission_classes = [IsHROrReadOnly]

    @extend_schema(summary='Generate salary slips for all employees in a payroll period')
    @action(detail=False, methods=['post'])
    def generate(self, request, period_id=None):
        from apps.payroll.models import PayrollPeriod, PayrollItem
        try:
            period = PayrollPeriod.objects.get(id=period_id)
        except PayrollPeriod.DoesNotExist:
            return Response({'success': False, 'message': 'Periode tidak ditemukan.'}, status=404)

        items = PayrollItem.objects.filter(period=period).select_related('employee', 'period__entity')
        generated, errors = 0, []

        for item in items:
            try:
                generate_slip_pdf(item)
                generated += 1
            except Exception as e:
                errors.append({'employee': item.employee.full_name, 'error': str(e)})

        return Response({
            'success': True,
            'generated': generated,
            'errors': errors,
        })
