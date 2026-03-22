"""
Views for service management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from apps.accounts.decorators import manager_required
from .models import Service
from .forms import ServiceForm


@login_required
def service_list_view(request):
    """
    List all services.
    """
    services = Service.objects.all().order_by('category', 'display_order', 'name')
    
    services_by_category = {}
    for s in services:
        label = s.get_category_display()
        services_by_category.setdefault(label, []).append(s)

    return render(request, 'services/service_list.html', {
        'services': services,
        'services_by_category': services_by_category,
    })


@manager_required
def service_create_view(request):
    """
    Create a new service (manager only).
    """
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service "{service.name}" created successfully.')
            return redirect('services:list')
    else:
        form = ServiceForm()
    
    return render(request, 'services/service_form.html', {
        'form': form,
        'title': 'Add New Service',
        'button_text': 'Create Service',
    })


@manager_required
def service_edit_view(request, pk):
    """
    Edit a service (manager only).
    """
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service "{service.name}" updated successfully.')
            return redirect('services:list')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'services/service_form.html', {
        'form': form,
        'title': f'Edit Service: {service.name}',
        'button_text': 'Save Changes',
        'service': service,
    })


@manager_required
@require_http_methods(["POST"])
def service_toggle_active_view(request, pk):
    """
    Toggle service active status (manager only).
    """
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=['is_active'])
    
    return JsonResponse({
        'success': True,
        'is_active': service.is_active,
        'message': f'Service {"activated" if service.is_active else "deactivated"} successfully'
    })


@manager_required
@require_http_methods(["POST"])
def service_delete_view(request, pk):
    """
    Delete a service (manager only).
    """
    service = get_object_or_404(Service, pk=pk)
    
    # Check if service is used in any jobs
    if service.jobs.exists():
        return JsonResponse({
            'success': False,
            'error': 'Cannot delete service that is used in existing jobs. Deactivate it instead.'
        })
    
    name = service.name
    service.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Service "{name}" deleted successfully'
    })


# API endpoints for AJAX
@login_required
def api_service_list(request):
    """
    API endpoint to get all active services as JSON.
    """
    category = request.GET.get('category')
    services = Service.objects.filter(is_active=True)
    
    if category:
        services = services.filter(category=category)
    
    data = [{
        'id': s.id,
        'name': s.name,
        'category': s.category,
        'category_display': s.get_category_display(),
        'price': float(s.price),
        'formatted_price': s.formatted_price,
        'estimated_duration': s.estimated_duration,
        'formatted_duration': s.formatted_duration,
    } for s in services]
    
    return JsonResponse({'services': data})
