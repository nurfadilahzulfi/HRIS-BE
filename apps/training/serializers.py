from rest_framework import serializers
from .models import TrainingCategory, TrainingProgram, TrainingParticipant


class TrainingCategorySerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)

    class Meta:
        model = TrainingCategory
        fields = ['id', 'entity', 'entity_name', 'name', 'description']
        read_only_fields = ['id']


class TrainingParticipantSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = TrainingParticipant
        fields = [
            'id', 'program', 'employee', 'employee_name', 'status', 'attendance',
            'score', 'kpi_snapshot', 'certificate', 'notes', 'registered_at', 'created_at'
        ]
        read_only_fields = ['id', 'kpi_snapshot', 'registered_at', 'created_at']


class TrainingProgramSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = TrainingProgram
        fields = [
            'id', 'entity', 'entity_name', 'category', 'category_name', 'title',
            'description', 'objectives', 'trainer', 'start_date', 'end_date',
            'location', 'max_participants', 'material', 'status', 'is_active',
            'participants_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_participants_count(self, obj):
        return obj.participants.count()

