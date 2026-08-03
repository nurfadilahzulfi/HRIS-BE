from rest_framework import serializers
from .models import Assessment, Question, Choice, AssessmentAttempt


class ChoiceTakeSerializer(serializers.ModelSerializer):
    """Dipakai saat karyawan mengerjakan ujian -- TIDAK ADA is_correct."""
    class Meta:
        model = Choice
        fields = ['id', 'text']
        read_only_fields = ['id']


class ChoiceAdminSerializer(serializers.ModelSerializer):
    """Dipakai HR/trainer mengelola bank soal -- memuat is_correct."""
    class Meta:
        model = Choice
        fields = ['id', 'question', 'text', 'is_correct']
        read_only_fields = ['id']


# Alias for backward compatibility
ChoiceSerializer = ChoiceAdminSerializer


class QuestionTakeSerializer(serializers.ModelSerializer):
    choices = ChoiceTakeSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'assessment', 'text', 'question_type', 'points', 'order', 'choices']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceAdminSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'assessment', 'text', 'question_type', 'points', 'order', 'choices']
        read_only_fields = ['id']


class AssessmentTakeSerializer(serializers.ModelSerializer):
    """Endpoint yang diakses karyawan saat mengambil ujian."""
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    questions = QuestionTakeSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'entity', 'entity_name', 'title', 'description', 'time_limit', 'questions']
        read_only_fields = ['id']


class AssessmentSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    training_title = serializers.CharField(source='training.title', read_only=True, default=None)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id', 'entity', 'entity_name', 'training', 'training_title', 'title',
            'description', 'passing_score', 'time_limit', 'is_mandatory', 'is_active',
            'questions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'participant', 'assessment', 'assessment_title', 'employee',
            'employee_name', 'started_at', 'submitted_at', 'score', 'is_passed', 'answers'
        ]
        read_only_fields = ['id', 'started_at', 'submitted_at', 'score', 'is_passed']

