"""
Views for customer and vehicle management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q

from apps.accounts.decorators import manager_required
from .models import Customer, Vehicle
from .forms import CustomerForm, VehicleForm, QuickCustomerVehicleForm


@login_required
def customer_list_view(request):
    """
    List all customers with search functionality.
    """
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(is_active=True)
    
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    
    customers = customers.order_by('-created_at')[:100]
    
    return render(request, 'customers/customer_list.html', {
        'customers': customers,
        'query': query,
    })


@login_required
def customer_detail_view(request, pk):
    """
    View customer details with vehicles and job history.
    """
    customer = get_object_or_404(Customer, pk=pk)
    vehicles = customer.vehicles.all()
    recent_jobs = customer.jobs.all().order_by('-created_at')[:10]
    
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'vehicles': vehicles,
        'recent_jobs': recent_jobs,
    })


@manager_required
def customer_create_view(request):
    """
    Create a new customer (manager only).
    """
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" created successfully.')
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': 'Add New Customer',
        'button_text': 'Create Customer',
    })


@manager_required
def customer_edit_view(request, pk):
    """
    Edit a customer (manager only).
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer "{customer.name}" updated successfully.')
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': f'Edit Customer: {customer.name}',
        'button_text': 'Save Changes',
        'customer': customer,
    })


@login_required
def vehicle_detail_view(request, pk):
    """
    View vehicle details with service history.
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)
    service_history = vehicle.jobs.all().order_by('-created_at')[:20]
    
    return render(request, 'customers/vehicle_detail.html', {
        'vehicle': vehicle,
        'service_history': service_history,
    })


@manager_required
def vehicle_create_view(request, customer_pk):
    """
    Add a vehicle to a customer (manager only).
    """
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            vehicle.save()
            messages.success(request, f'Vehicle "{vehicle.plate_number}" added successfully.')
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = VehicleForm()
    
    return render(request, 'customers/vehicle_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Add Vehicle for {customer.name}',
        'button_text': 'Add Vehicle',
    })


@manager_required
def vehicle_edit_view(request, pk):
    """
    Edit a vehicle (manager only).
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle "{vehicle.plate_number}" updated successfully.')
            return redirect('customers:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    
    return render(request, 'customers/vehicle_form.html', {
        'form': form,
        'customer': vehicle.customer,
        'vehicle': vehicle,
        'title': f'Edit Vehicle: {vehicle.plate_number}',
        'button_text': 'Save Changes',
    })


@manager_required
def quick_customer_vehicle_view(request):
    """
    Quick form to create customer and vehicle at once.
    """
    if request.method == 'POST':
        form = QuickCustomerVehicleForm(request.POST)
        if form.is_valid():
            customer, vehicle = form.save()
            messages.success(request, f'Customer "{customer.name}" and vehicle "{vehicle.plate_number}" created.')
            
            # Check if we should redirect to job creation
            if request.GET.get('next') == 'job':
                return redirect('jobs:create') + f'?customer={customer.pk}&vehicle={vehicle.pk}'
            
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = QuickCustomerVehicleForm()
    
    return render(request, 'customers/quick_form.html', {
        'form': form,
    })


# API endpoints for AJAX
@login_required
def api_customer_search(request):
    """
    Search customers by name or phone (AJAX).
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'customers': []})
    
    customers = Customer.objects.filter(
        is_active=True
    ).filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query)
    )[:10]
    
    data = [{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'total_visits': c.total_visits,
        'is_vip': c.is_vip,
    } for c in customers]
    
    return JsonResponse({'customers': data})


@login_required
def api_vehicle_search(request):
    """
    Search vehicles by plate number (AJAX).
    """
    query = request.GET.get('q', '')
    customer_id = request.GET.get('customer_id')
    
    vehicles = Vehicle.objects.filter(is_active=True)
    
    if customer_id:
        vehicles = vehicles.filter(customer_id=customer_id)
    
    if query:
        vehicles = vehicles.filter(plate_number__icontains=query)
    
    vehicles = vehicles[:10]
    
    data = [{
        'id': v.id,
        'plate_number': v.plate_number,
        'make': v.make,
        'model': v.model,
        'full_description': v.full_description,
        'customer_id': v.customer_id,
        'customer_name': v.customer.name,
    } for v in vehicles]
    
    return JsonResponse({'vehicles': data})


@login_required
def api_customer_vehicles(request, customer_pk):
    """
    Get all vehicles for a customer (AJAX).
    """
    customer = get_object_or_404(Customer, pk=customer_pk)
    vehicles = customer.vehicles.filter(is_active=True)
    
    data = [{
        'id': v.id,
        'plate_number': v.plate_number,
        'make': v.make,
        'model': v.model,
        'full_description': v.full_description,
    } for v in vehicles]
    
    return JsonResponse({'vehicles': data})
