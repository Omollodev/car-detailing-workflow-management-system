"""
URL patterns for workers app.
"""

from django.urls import path
from . import views

app_name = 'workers'

urlpatterns = [
    path('', views.worker_list_view, name='list'),
    path('<int:pk>/', views.worker_detail_view, name='detail'),
    path('<int:pk>/edit/', views.worker_edit_view, name='edit'),
    path('<int:pk>/toggle-availability/', views.worker_toggle_availability, name='toggle_availability'),
    
    # Worker's own jobs view
    path('my-jobs/', views.my_jobs_view, name='my_jobs'),
    
    # API
    path('api/available/', views.api_available_workers, name='api_available'),
    path('api/<int:pk>/status/', views.api_worker_status, name='api_status'),
]
