from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkScheduleViewSet, EmployeeScheduleViewSet, AttendanceLogViewSet

router = DefaultRouter()
router.register(r'attendance/schedules',       WorkScheduleViewSet,    basename='work-schedule')
router.register(r'attendance/employee-schedules', EmployeeScheduleViewSet, basename='employee-schedule')
router.register(r'attendance/logs',            AttendanceLogViewSet,   basename='attendance-log')

urlpatterns = [
    path('', include(router.urls)),
]
