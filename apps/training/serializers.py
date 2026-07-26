from rest_framework import serializers
from .models import TrainingProgram, TrainingParticipant


class TrainingParticipantSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = TrainingParticipant
        fields = ['id', 'program', 'employee', 'employee_name', 'status', 'score', 'certificate', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class TrainingProgramSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = TrainingProgram
        fields = [
            'id', 'entity', 'entity_name', 'title', 'description',
            'trainer', 'start_date', 'end_date', 'location', 'is_active',
            'participants_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_participants_count(self, obj):
        return obj.participants.count()
