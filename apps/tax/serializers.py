from rest_framework import serializers
from .models import PTKP, PPh21Bracket, TaxCalculationLog
from .engine import calculate_pph21


from django.utils import timezone
from apps.employees.models import Employee


class PTKPSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PTKP
        fields = ['id', 'year', 'status_code', 'amount']
        read_only_fields = ['id']


class PPh21BracketSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PPh21Bracket
        fields = ['id', 'year', 'income_from', 'income_to', 'rate']
        read_only_fields = ['id']


class TaxCalculationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TaxCalculationLog
        fields = [
            'id', 'payroll_item', 'scheme', 'ptkp_status', 'ptkp_amount',
            'gross_annual', 'biaya_jabatan', 'pkp_annual',
            'tax_annual', 'tax_monthly', 'detail', 'calculated_at',
        ]
        read_only_fields = [
            'id', 'payroll_item', 'scheme', 'ptkp_status', 'ptkp_amount',
            'gross_annual', 'biaya_jabatan', 'pkp_annual',
            'tax_annual', 'tax_monthly', 'detail', 'calculated_at',
        ]


class PPh21SimulateSerializer(serializers.Serializer):
    """Input untuk simulasi kalkulasi PPh21."""
    gross_monthly         = serializers.DecimalField(max_digits=15, decimal_places=2)
    ptkp_status           = serializers.ChoiceField(choices=Employee.PTKPStatus.choices, default=Employee.PTKPStatus.TK0)
    scheme                = serializers.ChoiceField(choices=['GROSS', 'GROSS_UP', 'NET'], default='GROSS')
    year                  = serializers.IntegerField(default=lambda: timezone.now().year)
    bpjs_employee_monthly = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
