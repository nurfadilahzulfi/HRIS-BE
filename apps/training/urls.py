from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainingProgramViewSet, TrainingParticipantViewSet

router = DefaultRouter()
router.register(r'training/programs', TrainingProgramViewSet, basename='training-program')
router.register(r'training/participants', TrainingParticipantViewSet, basename='training-participant')

urlpatterns = [
    path('', include(router.urls)),
]
