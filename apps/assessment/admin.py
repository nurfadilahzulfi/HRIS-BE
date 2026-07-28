from django.contrib import admin
from .models import Assessment, Question, Choice, AssessmentAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'entity', 'training', 'passing_score', 'time_limit', 'is_mandatory', 'is_active']
    list_filter = ['entity', 'is_mandatory', 'is_active']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'text', 'question_type', 'points', 'order']
    list_filter = ['assessment', 'question_type']
    search_fields = ['text']
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    list_filter = ['is_correct']


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ['employee', 'assessment', 'score', 'is_passed', 'started_at', 'submitted_at']
    list_filter = ['is_passed', 'assessment']
    search_fields = ['employee__full_name', 'assessment__title']
    readonly_fields = ['score', 'is_passed', 'started_at', 'submitted_at']

