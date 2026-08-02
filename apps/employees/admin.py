from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
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
        'position', 'status', 'join_date', 'get_user_account',
    ]
    list_filter   = ['entity', 'status', 'gender', 'department']
    search_fields = ['full_name', 'employee_id', 'nik', 'phone']
    readonly_fields = ['employee_id', 'created_at', 'updated_at', 'get_user_account_link']
    autocomplete_fields = ['department', 'position', 'manager']

    fieldsets = (
        ('Akun Login', {
            'fields': ('user', 'get_user_account_link'),
            'description': (
                'Hubungkan karyawan ini ke akun login. '
                'Setelah terhubung, karyawan dapat login ke sistem HRIS.'
            ),
        }),
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
            'fields': ('npwp', 'ptkp_status', 'pph21_scheme'),
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

    @admin.display(description='Akun Login')
    def get_user_account(self, obj):
        if obj.user:
            url = reverse('admin:core_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return format_html('<span style="color:#999;">— Belum terhubung —</span>')

    @admin.display(description='Link ke Akun User')
    def get_user_account_link(self, obj):
        if obj.user:
            url = reverse('admin:core_user_change', args=[obj.user.pk])
            return format_html(
                'Terhubung ke akun: <a href="{}" target="_blank"><strong>{}</strong></a>',
                url, obj.user.email,
            )
        return format_html(
            'Belum terhubung ke akun login. '
            'Pilih User di field "Akun Login" di atas.'
        )

    def save_model(self, request, obj, form, change):
        """After saving Employee, sync the User.employee FK so both sides are in sync."""
        super().save_model(request, obj, form, change)
        if obj.user and obj.user.employee_id != obj.pk:
            obj.user.employee = obj
            obj.user.save(update_fields=['employee'])
