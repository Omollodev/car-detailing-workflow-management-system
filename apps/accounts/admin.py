"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Additional Info'), {
            'fields': ('role', 'phone', 'profile_pic','is_active_worker')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Additional Info'), {
            'fields': ('role', 'phone', 'first_name', 'last_name', 'email')
        }),
    )
