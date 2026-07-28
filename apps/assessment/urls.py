from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, QuestionViewSet, ChoiceViewSet, AssessmentAttemptViewSet

router = DefaultRouter()
router.register(r'assessment/programs', AssessmentViewSet, basename='assessment-program')
router.register(r'assessment/questions', QuestionViewSet, basename='assessment-question')
router.register(r'assessment/choices', ChoiceViewSet, basename='assessment-choice')
router.register(r'assessment/attempts', AssessmentAttemptViewSet, basename='assessment-attempt')

urlpatterns = [
    path('', include(router.urls)),
]

