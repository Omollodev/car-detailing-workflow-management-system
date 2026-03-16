"""
API URL patterns for jobs app (used for AJAX polling).
"""

from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Dashboard data
    path('dashboard/stats/', api_views.dashboard_stats_api, name='dashboard_stats'),
    path('dashboard/jobs/', api_views.dashboard_jobs_api, name='dashboard_jobs'),
    
    # Job data
    path('jobs/<int:pk>/', api_views.job_detail_api, name='job_detail'),
    path('jobs/<int:pk>/timeline/', api_views.job_timeline_api, name='job_timeline'),
    
    # Alerts
    path('alerts/', api_views.alerts_api, name='alerts'),
]
