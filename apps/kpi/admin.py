from django.contrib import admin
from .models import KPITemplate, KPIItem, EmployeeKPIAssignment, EmployeeKPIResultItem


class KPIItemInline(admin.TabularInline):
    model = KPIItem
    extra = 0


@admin.register(KPITemplate)
class KPITemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'entity', 'department', 'period_type', 'is_active']
    list_filter = ['entity', 'period_type', 'is_active']
    search_fields = ['title']
    inlines = [KPIItemInline]
    filter_horizontal = ['applicable_positions']


class EmployeeKPIResultItemInline(admin.TabularInline):
    model = EmployeeKPIResultItem
    extra = 0
    readonly_fields = ['score']


@admin.register(EmployeeKPIAssignment)
class EmployeeKPIAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'template', 'period_year', 'period_index', 'context', 'status', 'final_score']
    list_filter = ['status', 'context', 'period_year']
    search_fields = ['employee__full_name', 'template__title']
    inlines = [EmployeeKPIResultItemInline]

