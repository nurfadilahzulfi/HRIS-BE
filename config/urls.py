"""HRIS Enterprise API URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

api_urlpatterns = [
    # Auth
    path('auth/', include('apps.core.urls')),
    # Company & Entity
    path('', include('apps.company.urls')),
    # Employees & Org Chart
    path('', include('apps.employees.urls')),
    # Contracts
    path('', include('apps.contracts.urls')),
    # Attendance
    path('', include('apps.attendance.urls')),
    # Leave
    path('', include('apps.leave.urls')),
    # Payroll
    path('', include('apps.payroll.urls')),
    # Tax (PPh21)
    path('', include('apps.tax.urls')),
    # Salary Slip
    path('', include('apps.salary_slip.urls')),
    # Training
    path('', include('apps.training.urls')),
    # Assessment
    path('', include('apps.assessment.urls')),
    # KPI
    path('', include('apps.kpi.urls')),
    # Notifications
    path('', include('apps.notifications.urls')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include(api_urlpatterns)),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
