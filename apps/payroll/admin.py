from django.contrib import admin
from .models import SalaryComponent, EmployeeSalaryComponent, OvertimeRecord, PayrollPeriod, PayrollItem


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'entity', 'component_type', 'formula_type', 'formula_value', 'is_taxable', 'is_active']
    list_filter   = ['entity', 'component_type', 'is_active']
    search_fields = ['name']


@admin.register(EmployeeSalaryComponent)
class EmployeeSalaryComponentAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'component', 'amount', 'is_active', 'effective_from']
    list_filter   = ['component__component_type', 'is_active']
    search_fields = ['employee__full_name', 'employee__employee_id']
    autocomplete_fields = ['employee', 'component']


@admin.register(OvertimeRecord)
class OvertimeRecordAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'date', 'hours_worked', 'overtime_type', 'amount', 'payroll_period']
    list_filter   = ['overtime_type', 'payroll_period']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['amount', 'created_at']
    date_hierarchy  = 'date'


class PayrollItemInline(admin.TabularInline):
    model   = PayrollItem
    extra   = 0
    readonly_fields = ['employee', 'gross_salary', 'total_deductions', 'net_salary', 'calculated_at']
    can_delete = False


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display  = ['entity', 'month', 'year', 'status', 'finalized_at', 'created_by']
    list_filter   = ['status', 'entity']
    readonly_fields = ['finalized_at', 'created_at', 'updated_at']
    inlines       = [PayrollItemInline]


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'period', 'pph21_scheme', 'gross_salary', 'total_deductions', 'net_salary']
    list_filter   = ['pph21_scheme', 'period__entity']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['breakdown', 'calculated_at', 'updated_at']
