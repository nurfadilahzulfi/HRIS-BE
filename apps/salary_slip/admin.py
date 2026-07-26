from django.contrib import admin
from .models import SignatureConfig, SalarySlip


@admin.register(SignatureConfig)
class SignatureConfigAdmin(admin.ModelAdmin):
    list_display  = ['entity', 'signer_name', 'signer_position', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display  = ['slip_number', 'payroll_item', 'is_signed', 'generated_at', 'is_sent', 'sent_at']
    list_filter   = ['is_signed', 'is_sent', 'payroll_item__period__entity']
    search_fields = ['slip_number', 'payroll_item__employee__full_name']
    readonly_fields = ['slip_number', 'generated_at', 'sent_at', 'created_at']
