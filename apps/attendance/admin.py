from django.contrib import admin
from .models import WorkSchedule, EmployeeSchedule, AttendanceLog


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display  = ['name', 'entity', 'work_start', 'work_end', 'break_duration', 'is_active']
    list_filter   = ['entity', 'is_active']
    search_fields = ['name']


@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'schedule', 'effective_from', 'effective_to']
    list_filter   = ['schedule']
    search_fields = ['employee__full_name', 'employee__employee_id']


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'date', 'check_in', 'check_out', 'source', 'late_minutes']
    list_filter   = ['source', 'date', 'employee__entity']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['created_at', 'updated_at', 'raw_data']
    date_hierarchy  = 'date'
