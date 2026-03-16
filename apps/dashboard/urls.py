"""
URL patterns for dashboard app.
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_index, name='index'),
    path('reports/', views.reports_view, name='reports'),
]
