from django.contrib import admin
from .models import PTKP, PPh21Bracket, TaxCalculationLog


@admin.register(PTKP)
class PTKPAdmin(admin.ModelAdmin):
    list_display  = ['status_code', 'year', 'amount']
    list_filter   = ['year']
    search_fields = ['status_code']


@admin.register(PPh21Bracket)
class PPh21BracketAdmin(admin.ModelAdmin):
    list_display  = ['year', 'income_from', 'income_to', 'rate']
    list_filter   = ['year']
    ordering      = ['year', 'income_from']


@admin.register(TaxCalculationLog)
class TaxCalculationLogAdmin(admin.ModelAdmin):
    list_display  = ['payroll_item', 'scheme', 'ptkp_status', 'tax_monthly', 'calculated_at']
    list_filter   = ['scheme', 'ptkp_status']
    readonly_fields = ['payroll_item', 'detail', 'calculated_at']
