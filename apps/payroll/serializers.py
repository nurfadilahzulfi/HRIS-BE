from rest_framework import serializers
from .models import SalaryComponent, EmployeeSalaryComponent, OvertimeRecord, PayrollPeriod, PayrollItem


class SalaryComponentSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)

    class Meta:
        model  = SalaryComponent
        fields = [
            'id', 'entity', 'entity_name', 'name', 'component_type',
            'is_taxable', 'is_fixed', 'formula_type', 'formula_value', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeSalaryComponentSerializer(serializers.ModelSerializer):
    employee_name  = serializers.CharField(source='employee.full_name', read_only=True)
    component_name = serializers.CharField(source='component.name', read_only=True)
    component_type = serializers.CharField(source='component.component_type', read_only=True)

    class Meta:
        model  = EmployeeSalaryComponent
        fields = [
            'id', 'employee', 'employee_name', 'component', 'component_name',
            'component_type', 'amount', 'is_active', 'effective_from',
        ]
        read_only_fields = ['id']


class OvertimeRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_no = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model  = OvertimeRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_no',
            'date', 'hours_worked', 'overtime_type', 'rate_multiplier',
            'amount', 'payroll_period', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'amount', 'created_at']


class PayrollPeriodSerializer(serializers.ModelSerializer):
    entity_name   = serializers.CharField(source='entity.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default=None)
    items_count   = serializers.SerializerMethodField()

    class Meta:
        model  = PayrollPeriod
        fields = [
            'id', 'entity', 'entity_name', 'month', 'year', 'status',
            'finalized_at', 'created_by', 'created_by_name',
            'items_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'finalized_at', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.count()


class PayrollItemSerializer(serializers.ModelSerializer):
    employee_name  = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_no = serializers.CharField(source='employee.employee_id', read_only=True)
    period_label   = serializers.SerializerMethodField()

    class Meta:
        model  = PayrollItem
        fields = [
            'id', 'period', 'period_label', 'employee', 'employee_name', 'employee_id_no',
            'pph21_scheme',
            'basic_salary', 'total_allowances', 'total_overtime', 'gross_salary',
            'bpjs_kes_employee', 'bpjs_kes_employer',
            'bpjs_jkk_employer', 'bpjs_jkm_employer',
            'bpjs_jht_employee', 'bpjs_jht_employer',
            'bpjs_jp_employee',  'bpjs_jp_employer',
            'pph21_amount', 'total_deductions', 'net_salary',
            'breakdown', 'calculated_at', 'updated_at',
        ]
        read_only_fields = ['id', 'calculated_at', 'updated_at']

    def get_period_label(self, obj):
        return f'{obj.period.month:02d}/{obj.period.year}'
