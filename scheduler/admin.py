from django.contrib import admin
from .models import Pipeline, Task, TaskExecution


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'pipeline', 'script_type', 'schedule_type', 'is_active']
    list_filter = ['pipeline', 'script_type', 'schedule_type', 'is_active']
    search_fields = ['name', 'description', 'script_path']
    filter_horizontal = ['depends_on']


@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ['task', 'pipeline', 'status', 'started_at', 'finished_at', 'duration', 'returncode']
    list_filter = ['status', 'started_at', 'task__pipeline']
    search_fields = ['task__name', 'error_message']
    readonly_fields = ['created_at', 'duration']
    date_hierarchy = 'created_at'

