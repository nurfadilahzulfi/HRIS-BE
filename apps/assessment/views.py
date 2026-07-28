from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import extend_schema
from django.utils import timezone

from apps.core.pagination import StandardResultsPagination
from .models import Assessment, Question, Choice, AssessmentAttempt
from .serializers import (
    AssessmentSerializer, QuestionSerializer, ChoiceSerializer, AssessmentAttemptSerializer
)


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['assessment'])
class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['entity', 'training', 'is_mandatory', 'is_active']
    search_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        qs = Assessment.objects.prefetch_related('questions__choices').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs

    @extend_schema(summary='Start assessment attempt for employee')
    @action(detail=True, methods=['post'], url_path='start', permission_classes=[permissions.IsAuthenticated])
    def start_assessment(self, request, pk=None):
        assessment = self.get_object()
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({'success': False, 'message': 'User tidak terhubung dengan profil karyawan.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing active/unsubmitted attempt
        active_attempt = AssessmentAttempt.objects.filter(
            assessment=assessment,
            employee=employee,
            submitted_at__isnull=True
        ).first()

        if active_attempt:
            attempt = active_attempt
        else:
            attempt = AssessmentAttempt.objects.create(
                assessment=assessment,
                employee=employee,
                started_at=timezone.now(),
                answers={}
            )

        serializer = AssessmentAttemptSerializer(attempt)
        return Response({
            'success': True,
            'message': 'Ujian berhasil dimulai.',
            'attempt': serializer.data,
            'questions': QuestionSerializer(assessment.questions.all(), many=True).data
        }, status=status.HTTP_201_CREATED if not active_attempt else status.HTTP_200_OK)


@extend_schema(tags=['assessment'])
class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filterset_fields = ['assessment', 'question_type']

    def get_queryset(self):
        return Question.objects.prefetch_related('choices').all()


@extend_schema(tags=['assessment'])
class ChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ChoiceSerializer
    permission_classes = [IsHROrReadOnly]

    def get_queryset(self):
        return Choice.objects.all()


@extend_schema(tags=['assessment'])
class AssessmentAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    filterset_fields = ['assessment', 'employee', 'participant', 'is_passed']

    def get_queryset(self):
        user = self.request.user
        qs = AssessmentAttempt.objects.select_related('assessment', 'employee', 'participant').all()
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            return qs.filter(assessment__entity=user.entity)
        return qs

    @extend_schema(summary='Submit answers and grade assessment attempt')
    @action(detail=True, methods=['post'], url_path='submit')
    def submit_attempt(self, request, pk=None):
        attempt = self.get_object()
        if attempt.submitted_at:
            return Response({'success': False, 'message': 'Ujian ini sudah disubmit sebelumnya.'}, status=status.HTTP_400_BAD_REQUEST)

        answers = request.data.get('answers', {})
        attempt.answers = answers
        attempt.submitted_at = timezone.now()
        self._grade_attempt(attempt)

        serializer = AssessmentAttemptSerializer(attempt)
        return Response({
            'success': True,
            'message': 'Ujian berhasil disubmit dan dinilai.',
            'data': serializer.data
        })

    def perform_create(self, serializer):
        attempt = serializer.save(submitted_at=timezone.now())
        self._grade_attempt(attempt)

    def _grade_attempt(self, attempt):
        assessment = attempt.assessment
        questions = assessment.questions.prefetch_related('choices').all()
        total_points = sum(q.points for q in questions)
        earned_points = 0

        for q in questions:
            user_choice_id = attempt.answers.get(str(q.id))
            if not user_choice_id:
                continue
            correct_choice = q.choices.filter(is_correct=True).first()
            if correct_choice and str(correct_choice.id) == str(user_choice_id):
                earned_points += q.points

        score = (earned_points / total_points * 100) if total_points > 0 else 0
        attempt.score = round(score, 2)
        attempt.is_passed = score >= float(assessment.passing_score)
        attempt.save(update_fields=['score', 'is_passed', 'submitted_at', 'answers'])
