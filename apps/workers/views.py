"""
Views for worker management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from apps.accounts.decorators import manager_required
from apps.accounts.models import User
from .models import WorkerProfile
from .forms import WorkerProfileForm, WorkerAssignmentForm


@login_required
def worker_list_view(request):
    """
    List all workers with their status.
    """
    workers = WorkerProfile.objects.select_related('user', 'current_job').all()
    
    return render(request, 'workers/worker_list.html', {
        'workers': workers,
    })


@login_required
def worker_detail_view(request, pk):
    """
    View worker details and performance metrics.
    """
    worker = get_object_or_404(WorkerProfile.objects.select_related('user'), pk=pk)
    recent_jobs = worker.assigned_jobs.order_by('-created_at')[:10]
    
    return render(request, 'workers/worker_detail.html', {
        'worker': worker,
        'recent_jobs': recent_jobs,
    })


@manager_required
def worker_edit_view(request, pk):
    """
    Edit worker profile (manager only).
    """
    worker = get_object_or_404(WorkerProfile, pk=pk)
    
    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, f'Worker profile for "{worker.name}" updated.')
            return redirect('workers:detail', pk=worker.pk)
    else:
        form = WorkerProfileForm(instance=worker)
    
    return render(request, 'workers/worker_form.html', {
        'form': form,
        'worker': worker,
        'title': f'Edit Worker: {worker.name}',
    })


@manager_required
@require_http_methods(["POST"])
def worker_toggle_availability(request, pk):
    """
    Toggle worker availability status (manager only).
    """
    worker = get_object_or_404(WorkerProfile, pk=pk)
    
    # Can't mark as available if they have a current job
    if not worker.is_available and worker.current_job:
        return JsonResponse({
            'success': False,
            'error': 'Worker has an active job. Complete or reassign it first.'
        })
    
    worker.is_available = not worker.is_available
    worker.save(update_fields=['is_available'])
    
    return JsonResponse({
        'success': True,
        'is_available': worker.is_available,
        'message': f'Worker is now {"available" if worker.is_available else "unavailable"}'
    })


@login_required
def my_jobs_view(request):
    """
    View for workers to see their assigned jobs.
    """
    if not hasattr(request.user, 'worker_profile'):
        messages.error(request, 'You do not have a worker profile.')
        return redirect('dashboard:index')
    
    worker = request.user.worker_profile
    active_jobs = worker.get_assigned_jobs().order_by('priority', 'created_at')
    completed_jobs = worker.get_completed_jobs().order_by('-completed_at')[:20]
    
    return render(request, 'workers/my_jobs.html', {
        'worker': worker,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
    })


# API endpoints for AJAX
@login_required
def api_available_workers(request):
    """
    Get list of available workers (AJAX).
    """
    workers = WorkerProfile.get_available_workers()
    
    data = [{
        'id': w.id,
        'name': w.name,
        'rating': float(w.rating),
        'jobs_today': w.get_job_count_today(),
        'skills': [s.name for s in w.skills.all()],
    } for w in workers]
    
    return JsonResponse({'workers': data})


@login_required
def api_worker_status(request, pk):
    """
    Get worker status (AJAX).
    """
    worker = get_object_or_404(WorkerProfile, pk=pk)
    
    data = {
        'id': worker.id,
        'name': worker.name,
        'is_available': worker.is_available,
        'is_busy': worker.is_busy,
        'current_job_id': worker.current_job_id,
        'current_job': str(worker.current_job) if worker.current_job else None,
        'jobs_today': worker.get_job_count_today(),
    }
    
    return JsonResponse(data)
