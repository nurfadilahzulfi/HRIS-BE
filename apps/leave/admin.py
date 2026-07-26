from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest, LeaveApproval


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'entity', 'max_days_per_year', 'is_paid', 'applicable_to', 'is_active']
    list_filter   = ['entity', 'applicable_to', 'is_paid', 'is_active']
    search_fields = ['name']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'leave_type', 'year', 'allocated', 'used', 'carry_forward']
    list_filter   = ['year', 'leave_type']
    search_fields = ['employee__full_name', 'employee__employee_id']


class LeaveApprovalInline(admin.TabularInline):
    model  = LeaveApproval
    extra  = 0
    readonly_fields = ['acted_at']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status']
    list_filter   = ['status', 'leave_type', 'employee__entity']
    search_fields = ['employee__full_name']
    readonly_fields = ['submitted_at', 'created_at', 'updated_at']
    inlines       = [LeaveApprovalInline]
    date_hierarchy  = 'start_date'
