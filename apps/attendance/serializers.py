from rest_framework import serializers
from .models import WorkSchedule, EmployeeSchedule, AttendanceLog


class WorkScheduleSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)

    class Meta:
        model  = WorkSchedule
        fields = ['id', 'entity', 'entity_name', 'name', 'work_start', 'work_end',
                  'break_duration', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmployeeScheduleSerializer(serializers.ModelSerializer):
    employee_name  = serializers.CharField(source='employee.full_name', read_only=True)
    schedule_name  = serializers.CharField(source='schedule.name', read_only=True)

    class Meta:
        model  = EmployeeSchedule
        fields = ['id', 'employee', 'employee_name', 'schedule', 'schedule_name',
                  'effective_from', 'effective_to']
        read_only_fields = ['id']


class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_no = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model  = AttendanceLog
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_no',
            'date', 'check_in', 'check_out', 'source',
            'late_minutes', 'early_minutes', 'work_minutes',
            'notes', 'raw_data', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'late_minutes', 'early_minutes', 'work_minutes', 'created_at', 'updated_at']


class AttendanceSyncSerializer(serializers.Serializer):
    """Input for POST /api/attendance/sync/ — accepts data from finger machine middleware."""
    employee_id = serializers.CharField(help_text='Employee ID (e.g. HO-2024-0001) or NIK')
    date        = serializers.DateField()
    check_in    = serializers.TimeField(required=False, allow_null=True)
    check_out   = serializers.TimeField(required=False, allow_null=True)
    source      = serializers.ChoiceField(choices=['FINGER', 'MANUAL', 'SYSTEM'], default='FINGER')
    raw_data    = serializers.DictField(required=False, allow_null=True)
    notes       = serializers.CharField(required=False, allow_blank=True)
