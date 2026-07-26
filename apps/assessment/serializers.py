from rest_framework import serializers
from .models import AssessmentTemplate, Question, AssessmentSubmission


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'template', 'prompt', 'options', 'correct_answer', 'weight']
        read_only_fields = ['id']


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentTemplate
        fields = ['id', 'entity', 'entity_name', 'title', 'description', 'passing_score', 'is_active', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']


class AssessmentSubmissionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    template_title = serializers.CharField(source='template.title', read_only=True)

    class Meta:
        model = AssessmentSubmission
        fields = ['id', 'template', 'template_title', 'employee', 'employee_name', 'answers', 'total_score', 'is_passed', 'submitted_at']
        read_only_fields = ['id', 'total_score', 'is_passed', 'submitted_at']
