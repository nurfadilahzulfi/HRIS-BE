from django.contrib import admin
from .models import TrainingProgram, TrainingParticipant


class TrainingParticipantInline(admin.TabularInline):
    model = TrainingParticipant
    extra = 0


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'entity', 'trainer', 'start_date', 'end_date', 'is_active']
    list_filter = ['entity', 'is_active']
    search_fields = ['title', 'trainer']
    inlines = [TrainingParticipantInline]


@admin.register(TrainingParticipant)
class TrainingParticipantAdmin(admin.ModelAdmin):
    list_display = ['program', 'employee', 'status', 'score']
    list_filter = ['status']
    search_fields = ['employee__full_name', 'program__title']
