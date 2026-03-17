"""
URL configuration for Car Detailing Workflow Management System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # App URLs
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('customers/', include('apps.customers.urls', namespace='customers')),
    path('jobs/', include('apps.jobs.urls', namespace='jobs')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('workers/', include('apps.workers.urls', namespace='workers')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    
    # API endpoints for AJAX
    path('api/', include('apps.jobs.api_urls', namespace='api')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
