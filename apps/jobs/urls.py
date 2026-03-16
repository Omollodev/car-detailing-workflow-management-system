"""
URL patterns for jobs app.
"""

from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Job CRUD
    path('', views.job_list_view, name='list'),
    path('create/', views.job_create_view, name='create'),
    path('<int:pk>/', views.job_detail_view, name='detail'),
    path('<int:pk>/edit/', views.job_edit_view, name='edit'),
    
    # Job actions
    path('<int:pk>/change-status/', views.job_change_status_view, name='change_status'),
    path('<int:pk>/assign-worker/', views.job_assign_worker_view, name='assign_worker'),
    path('<int:pk>/add-extra-service/', views.job_add_extra_service_view, name='add_extra_service'),
    path('<int:pk>/cancel/', views.job_cancel_view, name='cancel'),
    
    # Service actions
    path('<int:pk>/services/<int:service_pk>/complete/', views.job_service_complete_view, name='service_complete'),
    path('<int:pk>/services/<int:service_pk>/uncomplete/', views.job_service_uncomplete_view, name='service_uncomplete'),
]
