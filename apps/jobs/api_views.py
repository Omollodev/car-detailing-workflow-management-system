"""
API views for AJAX polling and real-time updates.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum

from apps.accounts.decorators import ajax_login_required
from .models import Job


@ajax_login_required
def dashboard_stats_api(request):
    """
    Return dashboard statistics for AJAX polling.
    """
    today = timezone.now().date()
    
    # Job counts by status
    stats = {
        'waiting': Job.objects.filter(status='waiting').count(),
        'in_progress': Job.objects.filter(status='in_progress').count(),
        'awaiting_extra': Job.objects.filter(status='awaiting_extra').count(),
        'completed_today': Job.objects.filter(
            status='completed',
            completed_at__date=today
        ).count(),
        'total_today': Job.objects.filter(created_at__date=today).count(),
        'need_alert': Job.objects.filter(need_alert=True).count(),
    }
    
    # Revenue today
    revenue = Job.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    stats['revenue_today'] = float(revenue)
    stats['timestamp'] = timezone.now().isoformat()
    
    return JsonResponse(stats)


@ajax_login_required
def dashboard_jobs_api(request):
    """
    Return jobs for dashboard Kanban view.
    """
    status = request.GET.get('status')
    
    jobs_qs = Job.objects.select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    )
    
    if status:
        jobs_qs = jobs_qs.filter(status=status)
    else:
        jobs_qs = jobs_qs.exclude(status__in=['completed', 'cancelled'])
    
    jobs_qs = jobs_qs.order_by('priority', 'created_at')[:50]
    
    jobs_data = []
    for job in jobs_qs:
        jobs_data.append({
            'id': job.id,
            'queue_number': job.queue_number,
            'status': job.status,
            'status_display': job.get_status_display(),
            'status_badge_class': job.status_badge_class,
            'priority': job.priority,
            'priority_display': job.get_priority_display(),
            'priority_badge_class': job.priority_badge_class,
            'customer_name': job.customer.name,
            'customer_phone': job.customer.phone,
            'vehicle_plate': job.vehicle.plate_number,
            'vehicle_description': job.vehicle.full_description,
            'worker_name': job.assigned_worker.name if job.assigned_worker else None,
            'need_alert': job.need_alert,
            'services_count': job.jobservice_set.count(),
            'pending_services': job.get_pending_services().count(),
            'estimated_duration': job.formatted_estimated_duration,
            'total_price': float(job.total_price),
            'formatted_price': job.formatted_total_price,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
        })
    
    return JsonResponse({
        'jobs': jobs_data,
        'timestamp': timezone.now().isoformat(),
    })


@ajax_login_required
def job_detail_api(request, pk):
    """
    Return job details for AJAX updates.
    """
    job = get_object_or_404(Job, pk=pk)
    
    services_data = []
    for js in job.jobservice_set.select_related('service', 'completed_by').all():
        services_data.append({
            'id': js.id,
            'service_name': js.service.name,
            'service_category': js.service.category,
            'is_completed': js.is_completed,
            'completed_at': js.completed_at.isoformat() if js.completed_at else None,
            'completed_by': js.completed_by.get_full_name() if js.completed_by else None,
            'price': float(js.effective_price),
            'notes': js.notes,
        })
    
    data = {
        'id': job.id,
        'status': job.status,
        'status_display': job.get_status_display(),
        'need_alert': job.need_alert,
        'has_pending_services': job.has_pending_services(),
        'has_pending_extra_services': job.has_pending_extra_services(),
        'services': services_data,
        'total_price': float(job.total_price),
        'amount_paid': float(job.amount_paid),
        'balance_due': float(job.balance_due),
        'payment_status': job.payment_status,
        'payment_status_display': job.get_payment_status_display(),
        'payment_channel': job.payment_channel,
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@ajax_login_required
def job_timeline_api(request, pk):
    """
    Return job timeline for AJAX updates.
    """
    job = get_object_or_404(Job, pk=pk)
    
    return JsonResponse({
        'timeline': job.get_timeline(),
        'timestamp': timezone.now().isoformat(),
    })


@ajax_login_required
def alerts_api(request):
    """
    Return alerts for jobs needing attention.
    """
    alerts = []
    
    # Jobs with pending extra services
    pending_extra = Job.objects.filter(
        need_alert=True
    ).exclude(
        status__in=['completed', 'cancelled']
    ).select_related('customer', 'vehicle')[:10]
    
    for job in pending_extra:
        pending_services = list(
            job.get_pending_services().filter(
                service__category__in=['detailing', 'additional'],
            ).values_list('service__name', flat=True)
        )
        alerts.append({
            'type': 'pending_extra',
            'job_id': job.id,
            'vehicle_plate': job.vehicle.plate_number,
            'customer_name': job.customer.name,
            'message': f'Pending extra services: {", ".join(pending_services)}',
            'created_at': job.created_at.isoformat(),
        })
    
    # Urgent jobs waiting
    urgent_waiting = Job.objects.filter(
        status='waiting',
        priority='urgent'
    ).select_related('customer', 'vehicle')[:5]
    
    for job in urgent_waiting:
        alerts.append({
            'type': 'urgent_waiting',
            'job_id': job.id,
            'vehicle_plate': job.vehicle.plate_number,
            'customer_name': job.customer.name,
            'message': 'Urgent job waiting for assignment',
            'created_at': job.created_at.isoformat(),
        })
    
    return JsonResponse({
        'alerts': alerts,
        'count': len(alerts),
        'timestamp': timezone.now().isoformat(),
    })
