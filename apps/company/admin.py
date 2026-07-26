from django.contrib import admin
from .models import Company, Entity


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display  = ('name', 'npwp', 'phone', 'email', 'created_at')
    search_fields = ('name', 'npwp')


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display  = ('code', 'name', 'company', 'payroll_cutoff_day', 'leave_approval_levels', 'is_active')
    list_filter   = ('company', 'is_active')
    search_fields = ('name', 'code')
