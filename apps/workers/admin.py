"""
Admin configuration for workers app.
"""

from django.contrib import admin
from .models import WorkerProfile


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    """Admin for WorkerProfile model."""
    
    list_display = ['user', 'is_available', 'current_job', 'rating', 'total_jobs_completed', 'employee_id']
    list_filter = ['is_available', 'hired_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    raw_id_fields = ['user', 'current_job']
    filter_horizontal = ['skills']
    readonly_fields = ['rating', 'total_ratings', 'total_jobs_completed', 'average_completion_time']
