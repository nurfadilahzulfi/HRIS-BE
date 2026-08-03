from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsHROrReadOnly
from apps.core.pagination import StandardResultsPagination
from .models import PTKP, PPh21Bracket, TaxCalculationLog
from .serializers import PTKPSerializer, PPh21BracketSerializer, TaxCalculationLogSerializer, PPh21SimulateSerializer
from .engine import calculate_pph21


@extend_schema(tags=['tax'])
class PTKPViewSet(viewsets.ModelViewSet):
    serializer_class   = PTKPSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filterset_fields   = ['year', 'status_code']

    def get_queryset(self):
        return PTKP.objects.all().order_by('year', 'status_code')


@extend_schema(tags=['tax'])
class PPh21BracketViewSet(viewsets.ModelViewSet):
    serializer_class   = PPh21BracketSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    filterset_fields   = ['year']

    def get_queryset(self):
        return PPh21Bracket.objects.all().order_by('year', 'income_from')


@extend_schema(tags=['tax'])
class TaxCalculationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = TaxCalculationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = StandardResultsPagination
    filterset_fields   = ['scheme', 'ptkp_status']

    def get_queryset(self):
        return TaxCalculationLog.objects.select_related('payroll_item__employee').all()

    @extend_schema(
        summary='Simulate PPh21 calculation (no data saved)',
        request=PPh21SimulateSerializer,
    )
    @action(detail=False, methods=['post'], url_path='simulate')
    def simulate(self, request):
        serializer = PPh21SimulateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = calculate_pph21(
            gross_monthly=data['gross_monthly'],
            ptkp_status=data['ptkp_status'],
            scheme=data['scheme'],
            year=data['year'],
            bpjs_employee_monthly=data['bpjs_employee_monthly'],
        )

        return Response({
            'success': True,
            'input': data,
            'result': {
                'tax_monthly':  float(result['tax_monthly']),
                'ptkp_amount':  float(result['ptkp_amount']),
                'pkp_annual':   float(result['pkp_annual']),
                'tax_annual':   float(result['tax_annual']),
                'biaya_jabatan': float(result['biaya_jabatan']),
                'detail':       result['detail'],
            }
        })
