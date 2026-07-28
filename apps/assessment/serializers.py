from rest_framework import serializers
from .models import Assessment, Question, Choice, AssessmentAttempt


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'question', 'text', 'is_correct']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'assessment', 'text', 'question_type', 'points', 'order', 'choices']
        read_only_fields = ['id']


class AssessmentSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    training_title = serializers.CharField(source='training.title', read_only=True)
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

