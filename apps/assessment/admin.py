from django.contrib import admin
from .models import AssessmentTemplate, Question, AssessmentSubmission


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'entity', 'passing_score', 'is_active']
    list_filter = ['entity', 'is_active']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'template', 'total_score', 'is_passed', 'submitted_at']
    list_filter = ['is_passed', 'template']
    search_fields = ['employee__full_name', 'template__title']
    readonly_fields = ['total_score', 'is_passed', 'submitted_at']
