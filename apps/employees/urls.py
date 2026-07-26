from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, PositionViewSet, EmployeeViewSet

router = DefaultRouter()
router.register(r'employees',   EmployeeViewSet,   basename='employee')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions',   PositionViewSet,   basename='position')

urlpatterns = [
    path('', include(router.urls)),
]
