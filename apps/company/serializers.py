from rest_framework import serializers
from .models import Company, Entity


class CompanySerializer(serializers.ModelSerializer):
    entities_count = serializers.IntegerField(source='entities.count', read_only=True)

    class Meta:
        model  = Company
        fields = [
            'id', 'name', 'logo', 'address', 'npwp',
            'phone', 'email', 'website', 'entities_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class EntitySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model  = Entity
        fields = [
            'id', 'company', 'company_name', 'name', 'code',
            'address', 'npwp', 'phone', 'email',
            'payroll_cutoff_day', 'leave_approval_levels',
            'employee_id_format', 'employee_id_seq_padding',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_employee_id_format(self, value):
        required_placeholders = ['{ENTITY_CODE}', '{YEAR}', '{SEQ}']
        missing = [p for p in required_placeholders if p not in value]
        if missing:
            raise serializers.ValidationError(
                f"Format ID Karyawan harus mengandung placeholder: {', '.join(missing)}"
            )
        return value


class EntityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for nested/list use."""
    class Meta:
        model  = Entity
        fields = ['id', 'name', 'code', 'is_active']
