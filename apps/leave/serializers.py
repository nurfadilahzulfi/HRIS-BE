from rest_framework import serializers
from .models import LeaveType, LeaveBalance, LeaveRequest, LeaveApproval


class LeaveTypeSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)

    class Meta:
        model  = LeaveType
        fields = [
            'id', 'entity', 'entity_name', 'name', 'max_days_per_year',
            'is_paid', 'applicable_to', 'allow_halfday', 'requires_attachment',
            'carry_forward_days', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name  = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    remaining      = serializers.IntegerField(read_only=True)

    class Meta:
        model  = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'year', 'allocated', 'used', 'carry_forward', 'remaining',
        ]
        read_only_fields = ['id', 'used']


class LeaveApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.full_name', read_only=True)

    class Meta:
        model  = LeaveApproval
        fields = ['id', 'level', 'approver', 'approver_name', 'status', 'notes', 'acted_at']
        read_only_fields = ['id', 'acted_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approvals       = LeaveApprovalSerializer(many=True, read_only=True)

    class Meta:
        model  = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'total_days', 'is_halfday',
            'reason', 'attachment', 'status', 'submitted_at',
            'approvals', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'submitted_at', 'created_at', 'updated_at']


class LeaveRequestListSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)

    class Meta:
        model  = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'total_days', 'status', 'submitted_at',
        ]


class ApproveRejectSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
