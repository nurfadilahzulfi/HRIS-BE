from django.contrib import admin
from .models import Department, Position, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'entity', 'head', 'is_active']
    list_filter   = ['entity', 'is_active']
    search_fields = ['name', 'code']
    autocomplete_fields = ['head']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display  = ['name', 'department', 'grade_level', 'is_active']
    list_filter   = ['department__entity', 'is_active']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = [
        'employee_id', 'full_name', 'entity', 'department',
        'position', 'status', 'join_date',
    ]
    list_filter   = ['entity', 'status', 'gender', 'department']
    search_fields = ['full_name', 'employee_id', 'nik', 'phone']
    readonly_fields = ['employee_id', 'created_at', 'updated_at']
    autocomplete_fields = ['department', 'position', 'manager']
    fieldsets = (
        ('Identitas', {
            'fields': ('entity', 'employee_id', 'full_name', 'nik', 'gender',
                       'date_of_birth', 'place_of_birth', 'religion', 'blood_type',
                       'marital_status', 'dependants', 'photo'),
        }),
        ('Kontak', {
            'fields': ('address', 'phone', 'emergency_contact'),
        }),
        ('Posisi', {
            'fields': ('department', 'position', 'manager'),
        }),
        ('Kepegawaian', {
            'fields': ('join_date', 'resign_date', 'status'),
        }),
        ('Pajak & PTKP', {
            'fields': ('npwp', 'ptkp_status'),
        }),
        ('BPJS', {
            'fields': ('bpjs_kes_no', 'bpjs_tk_no'),
        }),
        ('Bank', {
            'fields': ('bank_name', 'bank_account_no', 'bank_account_name'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
