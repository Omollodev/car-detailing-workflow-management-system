"""
URL patterns for notifications app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('<int:pk>/mark-read/', views.notification_mark_read_view, name='mark_read'),
    path('mark-all-read/', views.notification_mark_all_read_view, name='mark_all_read'),
    
    # API
    path('api/', views.api_notifications, name='api'),
]
