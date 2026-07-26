from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardResultsPagination
from .models import TrainingProgram, TrainingParticipant
from .serializers import TrainingProgramSerializer, TrainingParticipantSerializer


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['training'])
class TrainingProgramViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingProgramSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entity', 'is_active']
    search_fields = ['title', 'trainer', 'location']
    ordering_fields = ['start_date', 'title']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        qs = TrainingProgram.objects.select_related('entity').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['training'])
class TrainingParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingParticipantSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['program', 'employee', 'status']
    search_fields = ['employee__full_name']

    def get_queryset(self):
        user = self.request.user
        qs = TrainingParticipant.objects.select_related('program', 'employee').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(program__entity=user.entity)
        return qs
