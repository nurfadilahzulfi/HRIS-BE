from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardResultsPagination
from .models import AssessmentTemplate, Question, AssessmentSubmission
from .serializers import AssessmentTemplateSerializer, QuestionSerializer, AssessmentSubmissionSerializer


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['assessment'])
class AssessmentTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentTemplateSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['entity', 'is_active']
    search_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        qs = AssessmentTemplate.objects.prefetch_related('questions').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['assessment'])
class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filterset_fields = ['template']

    def get_queryset(self):
        return Question.objects.all()


@extend_schema(tags=['assessment'])
class AssessmentSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    filterset_fields = ['template', 'employee', 'is_passed']

    def get_queryset(self):
        user = self.request.user
        qs = AssessmentSubmission.objects.select_related('template', 'employee').all()
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            return qs.filter(template__entity=user.entity)
        return qs

    def perform_create(self, serializer):
        # Auto calculate score upon submit
        instance = serializer.save()
        template = instance.template
        questions = template.questions.all()
        total_weight = sum(q.weight for q in questions)
        correct_weight = 0

        for q in questions:
            user_ans = instance.answers.get(str(q.id))
            if user_ans and str(user_ans).strip().upper() == str(q.correct_answer).strip().upper():
                correct_weight += q.weight

        score = (correct_weight / total_weight * 100) if total_weight > 0 else 0
        instance.total_score = round(score, 2)
        instance.is_passed = score >= float(template.passing_score)
        instance.save(update_fields=['total_score', 'is_passed'])
