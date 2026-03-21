"""
Dashboard views for the main application interface.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import timedelta

from apps.jobs.models import Job
from apps.workers.models import WorkerProfile
from apps.customers.models import Customer


def landing_page(request):
    """
    Public landing page for unauthenticated users.
    """
    if request.user.is_authenticated:
        if getattr(request.user, 'is_customer', False):
            return redirect('customers:portal')
        return redirect('dashboard:index')
    
    return render(request, 'dashboard/landing.html')


@login_required
def dashboard_index(request):
    """
    Main dashboard with Kanban board and statistics.
    """
    user = request.user
    if getattr(user, 'is_customer', False):
        return redirect('customers:portal')

    today = timezone.now().date()
    
    # Job counts by status
    job_counts = {
        'waiting': Job.objects.filter(status='waiting').count(),
        'in_progress': Job.objects.filter(status='in_progress').count(),
        'awaiting_extra': Job.objects.filter(status='awaiting_extra').count(),
        'completed_today': Job.objects.filter(
            status='completed',
            completed_at__date=today
        ).count(),
    }
    
    # Jobs for Kanban columns
    waiting_jobs = Job.objects.filter(
        status='waiting'
    ).select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    ).order_by('priority', 'created_at')[:10]
    
    in_progress_jobs = Job.objects.filter(
        status='in_progress'
    ).select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    ).order_by('priority', 'started_at')[:10]
    
    awaiting_extra_jobs = Job.objects.filter(
        status='awaiting_extra'
    ).select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    ).order_by('priority', 'created_at')[:10]
    
    completed_jobs = Job.objects.filter(
        status='completed',
        completed_at__date=today
    ).select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    ).order_by('-completed_at')[:10]
    
    # Alerts - jobs needing attention
    alert_jobs = Job.objects.filter(
        need_alert=True
    ).exclude(
        status__in=['completed', 'cancelled']
    ).select_related('customer', 'vehicle')[:5]
    
    # Available workers
    available_workers = WorkerProfile.get_available_workers()
    
    # Today's statistics
    today_stats = Job.objects.filter(created_at__date=today).aggregate(
        total_jobs=Count('id'),
        total_revenue=Sum('total_price'),
    )
    
    context = {
        'job_counts': job_counts,
        'waiting_jobs': waiting_jobs,
        'in_progress_jobs': in_progress_jobs,
        'awaiting_extra_jobs': awaiting_extra_jobs,
        'completed_jobs': completed_jobs,
        'alert_jobs': alert_jobs,
        'available_workers': available_workers,
        'today_stats': today_stats,
        'today': today,
    }
    
    # Worker-specific view
    if user.is_worker and hasattr(user, 'worker_profile'):
        worker = user.worker_profile
        context['my_jobs'] = worker.get_assigned_jobs().order_by('priority', 'created_at')
        return render(request, 'dashboard/worker_dashboard.html', context)
    
    return render(request, 'dashboard/index.html', context)


@login_required
def reports_view(request):
    """
    Business reports and analytics (manager/admin only).
    """
    if not request.user.is_manager:
        return redirect('dashboard:index')
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Daily stats for the past week
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_jobs = Job.objects.filter(created_at__date=date)
        completed = day_jobs.filter(status='completed')
        
        daily_stats.append({
            'date': date,
            'total': day_jobs.count(),
            'completed': completed.count(),
            'revenue': completed.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        })
    
    # Weekly totals
    week_jobs = Job.objects.filter(created_at__date__gte=week_ago)
    week_completed = week_jobs.filter(status='completed')
    week_stats = {
        'total': week_jobs.count(),
        'completed': week_completed.count(),
        'revenue': week_completed.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'avg_duration': week_completed.aggregate(Avg('actual_duration'))['actual_duration__avg'] or 0,
    }
    
    # Monthly totals
    month_jobs = Job.objects.filter(created_at__date__gte=month_ago)
    month_completed = month_jobs.filter(status='completed')
    month_stats = {
        'total': month_jobs.count(),
        'completed': month_completed.count(),
        'revenue': month_completed.aggregate(Sum('total_price'))['total_price__sum'] or 0,
    }
    
    # Top workers (by jobs completed)
    top_workers = WorkerProfile.objects.annotate(
        jobs_count=Count('assigned_jobs', filter=Q(assigned_jobs__status='completed'))
    ).order_by('-jobs_count')[:5]
    
    # Top customers (by visits)
    top_customers = Customer.objects.order_by('-total_visits')[:10]
    
    context = {
        'daily_stats': daily_stats,
        'week_stats': week_stats,
        'month_stats': month_stats,
        'top_workers': top_workers,
        'top_customers': top_customers,
    }
    
    return render(request, 'dashboard/reports.html', context)
    