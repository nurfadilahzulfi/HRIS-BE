from rest_framework import serializers
from .models import Department, Position, Employee


class DepartmentSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    head_name   = serializers.CharField(source='head.full_name', read_only=True, default=None)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'entity', 'entity_name', 'name', 'code',
            'head', 'head_name', 'description', 'is_active',
            'employee_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_employee_count(self, obj):
        return obj.employees.filter(status=Employee.Status.ACTIVE).count()


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    entity_name     = serializers.CharField(source='department.entity.name', read_only=True)

    class Meta:
        model = Position
        fields = [
            'id', 'department', 'department_name', 'entity_name',
            'name', 'grade_level', 'description', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    entity_name     = serializers.CharField(source='entity.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    position_name   = serializers.CharField(source='position.name', read_only=True, default=None)
    manager_name    = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'entity_name',
            'department_name', 'position_name', 'manager_name',
            'gender', 'phone', 'join_date', 'status', 'photo',
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update."""
    entity_name     = serializers.CharField(source='entity.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    position_name   = serializers.CharField(source='position.name', read_only=True, default=None)
    manager_name    = serializers.CharField(source='manager.full_name', read_only=True, default=None)
    age             = serializers.IntegerField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            # Identity
            'id', 'employee_id', 'entity', 'entity_name',
            # Personal
            'full_name', 'nik', 'gender', 'date_of_birth', 'place_of_birth',
            'religion', 'blood_type', 'marital_status', 'dependants', 'age',
            # Contact
            'address', 'phone', 'emergency_contact', 'photo',
            # Position
            'department', 'department_name', 'position', 'position_name',
            'manager', 'manager_name',
            # Employment
            'join_date', 'resign_date', 'status',
            # Tax & PTKP
            'npwp', 'ptkp_status',
            # BPJS
            'bpjs_kes_no', 'bpjs_tk_no',
            # Bank
            'bank_name', 'bank_account_no', 'bank_account_name',
            # Timestamps
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']


class OrgChartSerializer(serializers.ModelSerializer):
    """Recursive serializer for org chart tree with cycle protection."""
    subordinates = serializers.SerializerMethodField()
    position_name   = serializers.CharField(source='position.name', read_only=True, default=None)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'photo',
            'position_name', 'department_name', 'subordinates',
        ]

    def get_subordinates(self, obj):
        visited = self.context.get('visited', set())
        if obj.pk in visited:
            return []
        visited.add(obj.pk)
        self.context['visited'] = visited

        subs = obj.subordinates.filter(status=Employee.Status.ACTIVE).select_related('position', 'department')
        return OrgChartSerializer(subs, many=True, context=self.context).data
