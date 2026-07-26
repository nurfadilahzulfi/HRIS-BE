from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignatureConfigViewSet, SalarySlipViewSet

router = DefaultRouter()
router.register(r'signature-configs', SignatureConfigViewSet, basename='signature-config')
router.register(r'salary-slips',      SalarySlipViewSet,      basename='salary-slip')

urlpatterns = [
    path('', include(router.urls)),
]
