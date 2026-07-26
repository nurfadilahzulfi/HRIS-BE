from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardResultsPagination
from .models import KPITemplate, KPIItem, EmployeeKPIAssignment, EmployeeKPIResultItem
from .serializers import (
    KPITemplateSerializer, KPIItemSerializer,
    EmployeeKPIAssignmentSerializer, EmployeeKPIResultItemSerializer
)


class IsHROrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


@extend_schema(tags=['kpi'])
class KPITemplateViewSet(viewsets.ModelViewSet):
    serializer_class = KPITemplateSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['entity', 'department', 'period_type', 'is_active']
    search_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        qs = KPITemplate.objects.prefetch_related('items').all()
        if user.role != 'SUPER_ADMIN' and user.entity:
            qs = qs.filter(entity=user.entity)
        return qs


@extend_schema(tags=['kpi'])
class KPIItemViewSet(viewsets.ModelViewSet):
    serializer_class = KPIItemSerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class = StandardResultsPagination
    filterset_fields = ['template']

    def get_queryset(self):
        return KPIItem.objects.all()


@extend_schema(tags=['kpi'])
class EmployeeKPIAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeKPIAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'template', 'period_year', 'status']

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeKPIAssignment.objects.select_related('template', 'employee').prefetch_related('results__kpi_item').all()
        if user.role == 'EMPLOYEE' and user.employee:
            return qs.filter(employee=user.employee)
        if user.role != 'SUPER_ADMIN' and user.entity:
            return qs.filter(template__entity=user.entity)
        return qs

    @extend_schema(summary='Evaluate and calculate final KPI score')
    @action(detail=True, methods=['post'], url_path='evaluate')
    def evaluate(self, request, pk=None):
        assignment = self.get_object()
        results_data = request.data.get('results', [])  # list of {kpi_item_id: X, actual_achievement: Y}
        notes = request.data.get('evaluator_notes', '')

        total_weighted_score = 0
        for res in results_data:
            item_id = res.get('kpi_item_id')
            actual = float(res.get('actual_achievement', 0))
            try:
                kpi_item = KPIItem.objects.get(id=item_id, template=assignment.template)
                target = float(kpi_item.target)
                weight = float(kpi_item.weight)
                pct_achieved = (actual / target) if target > 0 else 0
                item_score = min(pct_achieved * weight, weight * 1.2)  # capped at 120% per item

                EmployeeKPIResultItem.objects.update_or_create(
                    assignment=assignment,
                    kpi_item=kpi_item,
                    defaults={
                        'actual_achievement': actual,
                        'score': round(item_score, 2)
                    }
                )
                total_weighted_score += item_score
            except KPIItem.DoesNotExist:
                continue

        assignment.final_score = round(total_weighted_score, 2)
        assignment.evaluator_notes = notes
        assignment.status = EmployeeKPIAssignment.Status.FINAL
        assignment.save(update_fields=['final_score', 'evaluator_notes', 'status'])

        return Response({
            'success': True,
            'message': 'Evaluasi KPI berhasil disimpan.',
            'final_score': float(assignment.final_score)
        })
