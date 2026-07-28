from django.contrib import admin
from .models import TrainingCategory, TrainingProgram, TrainingParticipant


@admin.register(TrainingCategory)
class TrainingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity']
    list_filter = ['entity']
    search_fields = ['name']


class TrainingParticipantInline(admin.TabularInline):
    model = TrainingParticipant
    extra = 0


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'entity', 'category', 'trainer', 'start_date', 'end_date', 'status', 'is_active']
    list_filter = ['entity', 'category', 'status', 'is_active']
    search_fields = ['title', 'trainer']
    inlines = [TrainingParticipantInline]


@admin.register(TrainingParticipant)
class TrainingParticipantAdmin(admin.ModelAdmin):
    list_display = ['program', 'employee', 'status', 'attendance', 'score', 'registered_at']
    list_filter = ['status', 'attendance']
    search_fields = ['employee__full_name', 'program__title']

