"""
URL patterns for services app.
"""

from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list_view, name='list'),
    path('create/', views.service_create_view, name='create'),
    path('<int:pk>/edit/', views.service_edit_view, name='edit'),
    path('<int:pk>/toggle-active/', views.service_toggle_active_view, name='toggle_active'),
    path('<int:pk>/delete/', views.service_delete_view, name='delete'),
    
    # API
    path('api/list/', views.api_service_list, name='api_list'),
]
