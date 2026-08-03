from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class EmployeeInline(admin.StackedInline):
    """
    Inline Employee profile embedded directly inside the User change form.
    HR Admin can create or edit User + Employee data in a single page.
    Requires Employee.user OneToOneField (added in migration 0003).
    """
    from apps.employees.models import Employee
    model        = Employee
    can_delete   = False
    verbose_name = 'Profil Karyawan'
    verbose_name_plural = 'Profil Karyawan — Isi data kepegawaian di bawah ini'
    extra        = 1        # show 1 empty inline if no employee linked yet
    max_num      = 1
    show_change_link = True # quick link to full Employee detail page

    fieldsets = (
        ('Identitas & Kontak', {
            'fields': (
                'entity', 'full_name', 'nik', 'gender',
                'date_of_birth', 'place_of_birth', 'marital_status',
                'dependants', 'photo', 'address', 'phone', 'emergency_contact',
            ),
        }),
        ('Posisi & Kepegawaian', {
            'fields': (
                'department', 'position', 'manager',
                'join_date', 'status',
            ),
        }),
        ('Pajak, BPJS & Bank', {
            'fields': (
                'npwp', 'ptkp_status', 'pph21_scheme',
                'bpjs_kes_no', 'bpjs_tk_no',
                'bank_name', 'bank_account_no', 'bank_account_name',
            ),
        }),
    )

    def get_queryset(self, request):
        from apps.employees.models import Employee
        return Employee.objects.select_related('department', 'position', 'entity')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'get_full_name', 'role', 'entity', 'has_employee_profile', 'is_active', 'is_staff', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff', 'entity')
    search_fields = ('email',)
    ordering      = ('email',)
    inlines       = [EmployeeInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Role & Akses'), {'fields': ('role', 'entity')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'entity'),
            'description': (
                '⚠️ Setelah menyimpan akun, data karyawan (NIK, jabatan, BPJS, dll) '
                'dapat langsung diisi pada halaman edit user ini.'
            ),
        }),
    )

    @admin.display(description='Nama Lengkap')
    def get_full_name(self, obj):
        return obj.full_name or '-'

    @admin.display(description='Profil Karyawan', boolean=True)
    def has_employee_profile(self, obj):
        return hasattr(obj, 'employee_profile') and obj.employee_profile is not None

    def save_formset(self, request, form, formset, change):
        """
        After saving inline Employee, formset handles assigning Employee.user FK.
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if not getattr(instance, 'user_id', None):
                instance.user = form.instance
            instance.save()
        formset.save_m2m()
