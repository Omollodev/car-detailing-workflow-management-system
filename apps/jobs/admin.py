"""
Admin configuration for jobs app.
"""

from django.contrib import admin
from .models import Job, JobService, MpesaStkInitiation


class JobServiceInline(admin.TabularInline):
    """Inline admin for job services."""
    model = JobService
    extra = 1
    fields = ['service', 'is_completed', 'completed_at', 'completed_by', 'price_override', 'notes']
    readonly_fields = ['completed_at', 'completed_by']
    raw_id_fields = ['service']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin for Job model."""
    
    list_display = [
        'id', 'queue_number', 'customer', 'vehicle', 'status', 
        'priority', 'assigned_worker', 'need_alert', 'created_at'
    ]
    list_filter = ['status', 'priority', 'need_alert', 'payment_status', 'created_at']
    search_fields = ['customer__name', 'vehicle__plate_number', 'id']
    ordering = ['-created_at']
    raw_id_fields = ['customer', 'vehicle', 'assigned_worker', 'created_by']
    readonly_fields = [
        'queue_number', 'estimated_price', 'total_price', 
        'estimated_duration', 'actual_duration', 'timeline',
        'created_at', 'updated_at', 'started_at', 'completed_at'
    ]
    inlines = [JobServiceInline]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('customer', 'vehicle', 'assigned_worker', 'created_by', 'queue_number')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'need_alert')
        }),
        ('Instructions', {
            'fields': ('special_instructions', 'internal_notes')
        }),
        ('Pricing & payment', {
            'fields': (
                'estimated_price', 'discount', 'total_price',
                'payment_channel', 'payment_status', 'amount_paid',
                'mpesa_phone', 'mpesa_transaction_id',
            )
        }),
        ('Timing', {
            'fields': ('estimated_duration', 'actual_duration', 'created_at', 'started_at', 'completed_at')
        }),
        ('Timeline', {
            'fields': ('timeline',),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobService)
class JobServiceAdmin(admin.ModelAdmin):
    """Admin for JobService model."""
    
    list_display = ['job', 'service', 'is_completed', 'completed_at', 'effective_price']
    list_filter = ['is_completed', 'service__category']
    search_fields = ['job__id', 'service__name']
    raw_id_fields = ['job', 'service', 'completed_by']


@admin.register(MpesaStkInitiation)
class MpesaStkInitiationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'job',
        'amount',
        'phone',
        'status',
        'checkout_request_id',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['checkout_request_id', 'job__id', 'phone']
    raw_id_fields = ['job']
    readonly_fields = ['created_at', 'updated_at']
