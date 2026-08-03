from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsHROrReadOnly
from apps.core.pagination import StandardResultsPagination
from .models import Company, Entity
from .serializers import CompanySerializer, EntitySerializer


@extend_schema(tags=['company'])
class CompanyViewSet(viewsets.ModelViewSet):
    queryset           = Company.objects.all()
    serializer_class   = CompanySerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    search_fields      = ['name', 'npwp']
    ordering_fields    = ['name', 'created_at']
    ordering           = ['name']


@extend_schema(tags=['company'])
class EntityViewSet(viewsets.ModelViewSet):
    queryset           = Entity.objects.select_related('company').all()
    serializer_class   = EntitySerializer
    permission_classes = [IsHROrReadOnly]
    pagination_class   = StandardResultsPagination
    search_fields      = ['name', 'code']
    filterset_fields   = ['company', 'is_active']
    ordering_fields    = ['name', 'code', 'created_at']
    ordering           = ['name']

    def get_queryset(self):
        user = self.request.user
        # Super admin sees all; others see only their entity's company
        if user.role == 'SUPER_ADMIN':
            return super().get_queryset()
        if user.entity:
            return super().get_queryset().filter(company=user.entity.company)
        return Entity.objects.none()
