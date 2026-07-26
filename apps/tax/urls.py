from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PTKPViewSet, PPh21BracketViewSet, TaxCalculationLogViewSet

router = DefaultRouter()
router.register(r'tax/ptkp',       PTKPViewSet,              basename='ptkp')
router.register(r'tax/brackets',   PPh21BracketViewSet,       basename='pph21-bracket')
router.register(r'tax/logs',       TaxCalculationLogViewSet,  basename='tax-log')

urlpatterns = [
    path('', include(router.urls)),
]
