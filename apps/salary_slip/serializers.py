from rest_framework import serializers
from .models import SignatureConfig, SalarySlip


class SignatureConfigSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)

    class Meta:
        model  = SignatureConfig
        fields = ['id', 'entity', 'entity_name', 'signer_name', 'signer_position', 'signature_image', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class SalarySlipSerializer(serializers.ModelSerializer):
    employee_name  = serializers.CharField(source='payroll_item.employee.full_name', read_only=True)
    employee_id_no = serializers.CharField(source='payroll_item.employee.employee_id', read_only=True)
    period_label   = serializers.SerializerMethodField()
    net_salary     = serializers.DecimalField(source='payroll_item.net_salary', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model  = SalarySlip
        fields = [
            'id', 'slip_number', 'payroll_item',
            'employee_name', 'employee_id_no', 'period_label', 'net_salary',
            'pdf_file', 'is_signed', 'generated_at', 'is_sent', 'sent_at', 'created_at',
        ]
        read_only_fields = ['id', 'slip_number', 'generated_at', 'is_sent', 'sent_at', 'created_at']

    def get_period_label(self, obj):
        p = obj.payroll_item.period
        return f'{p.month:02d}/{p.year}'
