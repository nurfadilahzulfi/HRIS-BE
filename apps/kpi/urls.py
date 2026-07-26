from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KPITemplateViewSet, KPIItemViewSet, EmployeeKPIAssignmentViewSet

router = DefaultRouter()
router.register(r'kpi/templates', KPITemplateViewSet, basename='kpi-template')
router.register(r'kpi/items', KPIItemViewSet, basename='kpi-item')
router.register(r'kpi/assignments', EmployeeKPIAssignmentViewSet, basename='kpi-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
