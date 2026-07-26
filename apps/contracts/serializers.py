from rest_framework import serializers
from .models import Contract, ContractRenewal


class ContractRenewalSerializer(serializers.ModelSerializer):
    renewed_by_name = serializers.CharField(source='renewed_by.full_name', read_only=True, default=None)

    class Meta:
        model  = ContractRenewal
        fields = [
            'id', 'original_contract', 'new_end_date', 'new_salary_base',
            'document', 'notes', 'renewed_by', 'renewed_by_name', 'renewed_at',
        ]
        read_only_fields = ['id', 'renewed_at']


class ContractSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_no  = serializers.CharField(source='employee.employee_id', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    renewals        = ContractRenewalSerializer(many=True, read_only=True)

    class Meta:
        model  = Contract
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_no',
            'contract_type', 'start_date', 'end_date',
            'salary_base', 'document', 'status', 'notes',
            'days_until_expiry', 'renewals',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view."""
    employee_name  = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_no = serializers.CharField(source='employee.employee_id', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Contract
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_no',
            'contract_type', 'start_date', 'end_date',
            'salary_base', 'status', 'days_until_expiry',
        ]


class RenewContractSerializer(serializers.Serializer):
    """Input serializer for the /renew/ action."""
    new_end_date    = serializers.DateField()
    new_salary_base = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    document        = serializers.FileField(required=False)
    notes           = serializers.CharField(required=False, allow_blank=True)
