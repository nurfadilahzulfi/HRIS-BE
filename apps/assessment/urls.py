from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssessmentTemplateViewSet, QuestionViewSet, AssessmentSubmissionViewSet

router = DefaultRouter()
router.register(r'assessment/templates', AssessmentTemplateViewSet, basename='assessment-template')
router.register(r'assessment/questions', QuestionViewSet, basename='assessment-question')
router.register(r'assessment/submissions', AssessmentSubmissionViewSet, basename='assessment-submission')

urlpatterns = [
    path('', include(router.urls)),
]
