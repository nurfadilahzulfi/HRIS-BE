from rest_framework import serializers
from .models import KPITemplate, KPIItem, EmployeeKPIAssignment, EmployeeKPIResultItem


class KPIItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIItem
        fields = ['id', 'template', 'indicator', 'target', 'unit', 'weight', 'measurement_period']
        read_only_fields = ['id']


class KPITemplateSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    items = KPIItemSerializer(many=True, read_only=True)

    class Meta:
        model = KPITemplate
        fields = [
            'id', 'entity', 'entity_name', 'title', 'description', 'department', 'department_name',
            'applicable_positions', 'period_type', 'is_active', 'items', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeKPIResultItemSerializer(serializers.ModelSerializer):
    indicator = serializers.CharField(source='kpi_item.indicator', read_only=True)
    target = serializers.DecimalField(source='kpi_item.target', max_digits=10, decimal_places=2, read_only=True)
    unit = serializers.CharField(source='kpi_item.unit', read_only=True)
    weight = serializers.DecimalField(source='kpi_item.weight', max_digits=5, decimal_places=2, read_only=True)
    assessed_by_name = serializers.CharField(source='assessed_by.full_name', read_only=True, default=None)

    class Meta:
        model = EmployeeKPIResultItem
        fields = [
            'id', 'assignment', 'kpi_item', 'indicator', 'target', 'unit', 'weight',
            'actual_achievement', 'score', 'notes', 'assessed_by', 'assessed_by_name'
        ]
        read_only_fields = ['id', 'score']


class EmployeeKPIAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    template_title = serializers.CharField(source='template.title', read_only=True)
    training_title = serializers.CharField(source='related_training.title', read_only=True, default=None)
    results = EmployeeKPIResultItemSerializer(many=True, read_only=True)

    class Meta:
        model = EmployeeKPIAssignment
        fields = [
            'id', 'employee', 'employee_name', 'template', 'template_title', 'period_year',
            'period_index', 'status', 'context', 'related_training', 'training_title',
            'final_score', 'evaluator_notes', 'results', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'final_score', 'created_at', 'updated_at']

