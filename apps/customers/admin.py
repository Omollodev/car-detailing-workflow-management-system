"""
Admin configuration for customers app.
"""

from django.contrib import admin
from .models import Customer, Vehicle


class VehicleInline(admin.TabularInline):
    """Inline admin for vehicles on customer page."""
    model = Vehicle
    extra = 1
    fields = ['plate_number', 'make', 'model', 'year', 'color', 'vehicle_type', 'is_active']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin for Customer model."""
    
    list_display = ['name', 'phone', 'email', 'total_visits', 'total_spent', 'is_vip', 'is_active']
    list_filter = ['is_vip', 'is_active', 'created_at']
    search_fields = ['name', 'phone', 'email']
    ordering = ['-created_at']
    readonly_fields = ['total_visits', 'total_spent', 'created_at', 'updated_at']
    inlines = [VehicleInline]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin for Vehicle model."""
    
    list_display = ['plate_number', 'customer', 'make', 'model', 'year', 'vehicle_type', 'is_active']
    list_filter = ['vehicle_type', 'is_active', 'make']
    search_fields = ['plate_number', 'customer__name', 'make', 'model']
    ordering = ['-created_at']
    raw_id_fields = ['customer']
