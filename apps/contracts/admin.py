from django.contrib import admin
from .models import Contract, ContractRenewal


class ContractRenewalInline(admin.TabularInline):
    model   = ContractRenewal
    extra   = 0
    readonly_fields = ['renewed_by', 'renewed_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'contract_type', 'start_date', 'end_date', 'salary_base', 'status']
    list_filter   = ['contract_type', 'status', 'employee__entity']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['created_at', 'updated_at']
    inlines       = [ContractRenewalInline]
    fieldsets = (
        ('Informasi Kontrak', {
            'fields': ('employee', 'contract_type', 'start_date', 'end_date', 'salary_base'),
        }),
        ('Status & Dokumen', {
            'fields': ('status', 'document', 'notes'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ContractRenewal)
class ContractRenewalAdmin(admin.ModelAdmin):
    list_display  = ['original_contract', 'new_end_date', 'new_salary_base', 'renewed_by', 'renewed_at']
    readonly_fields = ['renewed_at']
