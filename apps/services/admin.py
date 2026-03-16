"""
Admin configuration for services app.
"""

from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin for Service model."""
    
    list_display = ['name', 'category', 'price', 'estimated_duration', 'is_active', 'display_order']
    list_filter = ['category', 'is_active', 'requires_special_equipment']
    search_fields = ['name', 'description']
    ordering = ['category', 'display_order', 'name']
    list_editable = ['is_active', 'display_order']
