from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryComponentViewSet, EmployeeSalaryComponentViewSet, OvertimeRecordViewSet, PayrollPeriodViewSet

router = DefaultRouter()
router.register(r'payroll/components',          SalaryComponentViewSet,         basename='salary-component')
router.register(r'payroll/employee-components', EmployeeSalaryComponentViewSet,  basename='employee-salary-component')
router.register(r'payroll/periods',             PayrollPeriodViewSet,            basename='payroll-period')
router.register(r'overtime/records',            OvertimeRecordViewSet,           basename='overtime-record')

urlpatterns = [
    path('', include(router.urls)),
]
