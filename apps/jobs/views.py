"""
Views for job management and workflow.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from apps.accounts.decorators import manager_required
from apps.notifications.models import Notification
from .models import Job, JobService
from .forms import (
    JobCreateForm, JobEditForm, JobStatusChangeForm,
    JobAssignWorkerForm, AddExtraServiceForm, JobServiceCompleteForm,
)


def _user_can_complete_job_services(user, job):
    """Staff only: managers/admins or the assigned worker."""
    if getattr(user, 'is_customer', False):
        return False
    if user.is_manager:
        return True
    if user.is_worker:
        wp = getattr(user, 'worker_profile', None)
        return bool(wp and job.assigned_worker_id == wp.pk)
    return False


@login_required
def job_list_view(request):
    """
    List all jobs with filtering options.
    """
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('q', '')

    jobs = Job.objects.select_related(
        'customer', 'vehicle', 'assigned_worker__user'
    ).all()

    if getattr(request.user, 'is_customer', False):
        profile = getattr(request.user, 'customer_profile', None)
        jobs = jobs.filter(customer=profile) if profile else jobs.none()

    # Counts before status/priority/search filters (sidebar / filters)
    status_counts = {
        'waiting': jobs.filter(status='waiting').count(),
        'in_progress': jobs.filter(status='in_progress').count(),
        'awaiting_extra': jobs.filter(status='awaiting_extra').count(),
        'completed': jobs.filter(status='completed').count(),
    }

    if status_filter:
        jobs = jobs.filter(status=status_filter)

    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)

    if search_query:
        jobs = jobs.filter(
            Q(vehicle__plate_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query)
        )

    jobs = jobs.order_by('-created_at')[:100]
    
    return render(request, 'jobs/job_list.html', {
        'jobs': jobs,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_counts': status_counts,
    })


@login_required
def job_detail_view(request, pk):
    """
    View job details with all services and timeline.
    """
    job = get_object_or_404(
        Job.objects.select_related(
            'customer', 'vehicle', 'assigned_worker__user', 'created_by'
        ).prefetch_related('jobservice_set__service'),
        pk=pk
    )

    if getattr(request.user, 'is_customer', False):
        profile = getattr(request.user, 'customer_profile', None)
        if not profile or job.customer_id != profile.pk:
            messages.error(request, 'You do not have access to this job.')
            return redirect('customers:portal')

    # Forms for various actions
    status_form = JobStatusChangeForm(initial={'status': job.status})
    assign_form = JobAssignWorkerForm()
    extra_service_form = AddExtraServiceForm()
    
    # Get services grouped by category
    basic_services = job.get_basic_services()
    extra_services = job.get_extra_services()
    
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'status_form': status_form,
        'assign_form': assign_form,
        'extra_service_form': extra_service_form,
        'basic_services': basic_services,
        'extra_services': extra_services,
        'timeline': job.get_timeline(),
    })


@manager_required
def job_create_view(request):
    """
    Create a new job (manager only).
    """
    if request.method == 'POST':
        form = JobCreateForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            
            # Add selected services
            services = form.cleaned_data.get('services', [])
            for service in services:
                JobService.objects.create(job=job, service=service)
            
            # Calculate totals
            job.calculate_totals()
            
            # Notify assigned worker
            if job.assigned_worker:
                Notification.create_notification(
                    recipient=job.assigned_worker.user,
                    notification_type=Notification.NotificationType.JOB_ASSIGNED,
                    title='New Job Assigned',
                    message=f'You have been assigned to Job #{job.id} - {job.vehicle.plate_number}',
                    job=job
                )
            
            messages.success(request, f'Job #{job.id} created successfully.')
            return redirect('jobs:detail', pk=job.pk)
    else:
        # Pre-populate from query params
        initial = {}
        if 'customer' in request.GET:
            initial['customer'] = request.GET['customer']
        if 'vehicle' in request.GET:
            initial['vehicle'] = request.GET['vehicle']
        
        form = JobCreateForm(initial=initial)
    
    return render(request, 'jobs/job_form.html', {
        'form': form,
        'title': 'Create New Job',
    })


@manager_required
def job_edit_view(request, pk):
    """
    Edit job details (manager only).
    """
    job = get_object_or_404(Job, pk=pk)
    
    if job.status in ['completed', 'cancelled']:
        messages.warning(request, 'Cannot edit completed or cancelled jobs.')
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobEditForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            job.calculate_totals()
            messages.success(request, f'Job #{job.id} updated successfully.')
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobEditForm(instance=job)
    
    return render(request, 'jobs/job_edit.html', {
        'form': form,
        'job': job,
    })


@login_required
@require_http_methods(["POST"])
def job_change_status_view(request, pk):
    """
    Change job status.
    """
    if getattr(request.user, 'is_customer', False):
        messages.error(request, 'You cannot change job status.')
        return redirect('jobs:detail', pk=pk)

    if not (request.user.is_worker or request.user.is_manager):
        messages.error(request, 'You cannot change job status.')
        return redirect('jobs:detail', pk=pk)

    job = get_object_or_404(Job, pk=pk)
    form = JobStatusChangeForm(request.POST)
    
    if form.is_valid():
        new_status = form.cleaned_data['status']
        notes = form.cleaned_data.get('notes', '')
        
        # Check for pending extra services when completing
        if new_status == 'completed' and job.has_pending_extra_services():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot complete job with pending extra services.',
                    'pending_services': list(
                        job.get_pending_services().values_list('service__name', flat=True)
                    )
                })
            messages.error(request, 'Cannot complete job with pending extra services.')
            return redirect('jobs:detail', pk=job.pk)
        
        if job.change_status(new_status, user=request.user, notes=notes):
            # Update worker status if needed
            if new_status == 'in_progress' and job.assigned_worker:
                job.assigned_worker.set_current_job(job)
            elif new_status in ['completed', 'cancelled'] and job.assigned_worker:
                job.assigned_worker.clear_current_job()
                job.assigned_worker.update_performance_metrics()
                
                # Update customer loyalty stats
                if new_status == 'completed':
                    job.customer.update_loyalty_stats()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'status': job.status,
                    'status_display': job.get_status_display(),
                    'status_badge_class': job.status_badge_class,
                })
            
            messages.success(request, f'Job status changed to {job.get_status_display()}.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid status transition.'
                })
            messages.error(request, 'Invalid status transition.')
    
    return redirect('jobs:detail', pk=job.pk)


@manager_required
@require_http_methods(["POST"])
def job_assign_worker_view(request, pk):
    """
    Assign or reassign a worker to a job.
    """
    job = get_object_or_404(Job, pk=pk)
    form = JobAssignWorkerForm(request.POST)
    
    if form.is_valid():
        new_worker = form.cleaned_data['worker']
        old_worker = job.assigned_worker
        
        # Clear old worker assignment
        if old_worker:
            old_worker.clear_current_job()
        
        # Assign new worker
        job.assigned_worker = new_worker
        job.save(update_fields=['assigned_worker'])
        
        # Add timeline event
        job.add_timeline_event(
            event_type='worker_assigned',
            description=f'Worker assigned: {new_worker.name}',
            user=request.user
        )
        job.save(update_fields=['timeline'])
        
        # Notify new worker
        Notification.create_notification(
            recipient=new_worker.user,
            notification_type=Notification.NotificationType.JOB_ASSIGNED,
            title='Job Assigned',
            message=f'You have been assigned to Job #{job.id} - {job.vehicle.plate_number}',
            job=job
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'worker_name': new_worker.name,
            })
        
        messages.success(request, f'Worker {new_worker.name} assigned to job.')
    
    return redirect('jobs:detail', pk=job.pk)


@manager_required
@require_http_methods(["POST"])
def job_add_extra_service_view(request, pk):
    """
    Add an extra service to an existing job.
    """
    job = get_object_or_404(Job, pk=pk)
    form = AddExtraServiceForm(request.POST)
    
    if form.is_valid():
        service = form.cleaned_data['service']
        notes = form.cleaned_data.get('notes', '')
        price_override = form.cleaned_data.get('price_override')
        
        # Check if service already exists
        if JobService.objects.filter(job=job, service=service).exists():
            messages.warning(request, f'Service "{service.name}" is already added to this job.')
            return redirect('jobs:detail', pk=job.pk)
        
        # Create job service
        JobService.objects.create(
            job=job,
            service=service,
            notes=notes,
            price_override=price_override
        )
        
        # Update job status and totals
        if job.status == 'in_progress':
            job.status = Job.Status.AWAITING_EXTRA
        job.update_alert_flag()
        job.save(update_fields=['status', 'need_alert'])
        job.calculate_totals()
        
        # Add timeline event
        job.add_timeline_event(
            event_type='extra_service_added',
            description=f'Extra service added: {service.name}',
            user=request.user,
            notes=notes
        )
        job.save(update_fields=['timeline'])
        
        # Notify worker
        if job.assigned_worker:
            Notification.create_notification(
                recipient=job.assigned_worker.user,
                notification_type=Notification.NotificationType.EXTRA_SERVICE,
                title='Extra Service Added',
                message=f'Extra service "{service.name}" added to Job #{job.id}',
                job=job
            )
        
        messages.success(request, f'Extra service "{service.name}" added.')
    
    return redirect('jobs:detail', pk=job.pk)


@login_required
@require_http_methods(["POST"])
def job_service_complete_view(request, pk, service_pk):
    """
    Mark a job service as complete.
    """
    job = get_object_or_404(Job, pk=pk)
    job_service = get_object_or_404(JobService, pk=service_pk, job=job)

    if not _user_can_complete_job_services(request.user, job):
        messages.error(request, 'You cannot update services on this job.')
        return redirect('jobs:detail', pk=job.pk)

    form = JobServiceCompleteForm(request.POST, request.FILES)
    
    if form.is_valid():
        if form.cleaned_data.get('photo'):
            job_service.photo = form.cleaned_data['photo']
        if form.cleaned_data.get('notes'):
            job_service.notes = form.cleaned_data['notes']
        
        job_service.mark_complete(user=request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'service_name': job_service.service.name,
                'pending_count': job.get_pending_services().count(),
            })
        
        messages.success(request, f'Service "{job_service.service.name}" marked as complete.')
    
    return redirect('jobs:detail', pk=job.pk)


@login_required
@require_http_methods(["POST"])
def job_service_uncomplete_view(request, pk, service_pk):
    """
    Mark a job service as incomplete (undo completion).
    """
    job = get_object_or_404(Job, pk=pk)
    job_service = get_object_or_404(JobService, pk=service_pk, job=job)

    if not _user_can_complete_job_services(request.user, job):
        messages.error(request, 'You cannot update services on this job.')
        return redirect('jobs:detail', pk=job.pk)

    job_service.mark_incomplete(user=request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'service_name': job_service.service.name,
        })
    
    messages.info(request, f'Service "{job_service.service.name}" marked as incomplete.')
    return redirect('jobs:detail', pk=job.pk)


@manager_required
@require_http_methods(["POST"])
def job_cancel_view(request, pk):
    """
    Cancel a job (manager only).
    """
    job = get_object_or_404(Job, pk=pk)
    reason = request.POST.get('reason', '')
    
    if job.change_status('cancelled', user=request.user, notes=reason):
        # Clear worker assignment
        if job.assigned_worker:
            job.assigned_worker.clear_current_job()
        
        messages.success(request, f'Job #{job.id} has been cancelled.')
    else:
        messages.error(request, 'Cannot cancel this job.')
    
    return redirect('jobs:detail', pk=job.pk)
