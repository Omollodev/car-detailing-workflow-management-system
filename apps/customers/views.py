"""
Views for customer and vehicle management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q

from apps.accounts.decorators import manager_required, customer_required
from apps.jobs.forms import CustomerJobBookingForm
from apps.jobs.models import Job, JobService

from .models import Customer, Vehicle
from .forms import (
    CustomerForm,
    VehicleForm,
    QuickCustomerVehicleForm,
    CustomerPortalProfileForm,
    CustomerMpesaPaymentForm,
    PaymentMethodSelectionForm,
)


@login_required
def customer_list_view(request):
    """
    List all customers with search functionality.
    """
    if getattr(request.user, 'is_customer', False):
        return redirect('customers:portal')

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
    if getattr(request.user, 'is_customer', False):
        profile = getattr(request.user, 'customer_profile', None)
        if not profile or customer.pk != profile.pk:
            messages.error(request, 'You do not have access to this page.')
            return redirect('customers:portal')
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
                url = reverse('jobs:create')
                return redirect(f'{url}?customer={customer.pk}&vehicle={vehicle.pk}')
            
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
    if getattr(request.user, 'is_customer', False):
        profile = getattr(request.user, 'customer_profile', None)
        if not profile or profile.pk != customer_pk:
            return JsonResponse({'error': 'Forbidden'}, status=403)
    vehicles = customer.vehicles.filter(is_active=True)
    
    data = [{
        'id': v.id,
        'plate_number': v.plate_number,
        'make': v.make,
        'model': v.model,
        'full_description': v.full_description,
    } for v in vehicles]
    
    return JsonResponse({'vehicles': data})


@login_required
@customer_required
def customer_portal_view(request):
    """Customer dashboard: profile summary, vehicles, recent jobs."""
    customer = getattr(request.user, 'customer_profile', None)
    if not customer:
        messages.error(
            request,
            'Your account has no customer profile. Please contact the shop.',
        )
        return redirect('accounts:logout')

    recent_jobs = customer.jobs.order_by('-created_at')[:20]
    return render(request, 'customers/portal.html', {
        'customer': customer,
        'recent_jobs': recent_jobs,
    })


@login_required
@customer_required
def customer_portal_profile_view(request):
    """Update store / contact details for the logged-in customer."""
    customer = request.user.customer_profile
    if request.method == 'POST':
        form = CustomerPortalProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your details were saved.')
            return redirect('customers:portal')
    else:
        form = CustomerPortalProfileForm(instance=customer)
    return render(request, 'customers/portal_profile.html', {
        'form': form,
        'customer': customer,
    })


@login_required
@customer_required
def customer_portal_vehicle_add_view(request):
    """Add a vehicle to the logged-in customer's account."""
    customer = request.user.customer_profile
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            vehicle.save()
            messages.success(request, f'Vehicle {vehicle.plate_number} added.')
            return redirect('customers:portal')
    else:
        form = VehicleForm()
    return render(request, 'customers/portal_vehicle_form.html', {
        'form': form,
        'customer': customer,
        'title': 'Add vehicle',
    })


@login_required
@customer_required
def customer_book_job_view(request):
    """Book a detailing job: choose vehicle and services."""
    customer = request.user.customer_profile
    if not customer.vehicles.filter(is_active=True).exists():
        messages.warning(
            request,
            'Add at least one vehicle before booking a service.',
        )
        return redirect('customers:portal_vehicle_add')

    if request.method == 'POST':
        form = CustomerJobBookingForm(customer, request.POST)
        if form.is_valid():
            job = Job.objects.create(
                customer=customer,
                vehicle=form.cleaned_data['vehicle'],
                created_by=request.user,
                priority=form.cleaned_data['priority'],
                special_instructions=form.cleaned_data.get(
                    'special_instructions', ''
                ),
            )
            for service in form.cleaned_data['services']:
                JobService.objects.create(job=job, service=service)
            job.calculate_totals()
            messages.success(
                request,
                f'Your booking request #{job.id} was submitted. We will confirm shortly.',
            )
            # Redirect to payment method selection
            return redirect('customers:job_select_payment_method', job_pk=job.pk)
    else:
        form = CustomerJobBookingForm(customer)

    return render(request, 'customers/book_job.html', {
        'form': form,
        'customer': customer,
    })


@login_required
@customer_required
def customer_job_select_payment_method_view(request, job_pk):
    """
    Customer selects payment method (M-Pesa or Cash) for their job.
    """
    customer = request.user.customer_profile
    job = get_object_or_404(
        Job.objects.select_related('customer', 'vehicle'),
        pk=job_pk,
        customer=customer,
    )

    if request.method == 'POST':
        form = PaymentMethodSelectionForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Set payment channel based on selection
            if payment_method == 'mpesa':
                job.payment_channel = Job.PaymentChannel.MPESA
                job.save(update_fields=['payment_channel'])
                messages.success(
                    request,
                    f'Payment method set to M-Pesa. Proceed to pay when ready.',
                )
                # For M-Pesa, show M-Pesa payment form next
                return redirect('customers:job_pay_mpesa', job_pk=job.pk)
            else:  # cash
                job.payment_channel = Job.PaymentChannel.CASH
                job.save(update_fields=['payment_channel'])
                messages.info(
                    request,
                    f'Payment method set to Cash. The manager will record your payment when you visit the shop.',
                )
                # For Cash, just return to job detail
                return redirect('jobs:detail', pk=job.pk)
    else:
        form = PaymentMethodSelectionForm()

    return render(request, 'customers/job_select_payment_method.html', {
        'form': form,
        'job': job,
        'customer': customer,
    })


@login_required
@customer_required
def customer_job_mpesa_pay_view(request, job_pk):
    """
    Record M-Pesa payment from the customer portal (immediate balance update).
    Cash payments are recorded by a manager on the job edit page.
    """
    customer = request.user.customer_profile
    job = get_object_or_404(
        Job.objects.select_related('customer', 'vehicle'),
        pk=job_pk,
        customer=customer,
    )

    if job.balance_due <= 0:
        messages.info(request, 'This job has no balance due.')
        return redirect('jobs:detail', pk=job.pk)

    if job.status in ('completed', 'cancelled'):
        messages.warning(request, 'Online payment is not available for this job.')
        return redirect('jobs:detail', pk=job.pk)

    if request.method == 'POST':
        form = CustomerMpesaPaymentForm(request.POST, job=job)
        if form.is_valid():
            job.apply_mpesa_payment(
                form.cleaned_data['amount'],
                phone=form.cleaned_data['mpesa_phone'],
                transaction_id=form.cleaned_data['mpesa_transaction_id'],
                user=request.user,
            )
            messages.success(
                request,
                'M-Pesa payment recorded. Thank you! Staff may verify the transaction if needed.',
            )
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = CustomerMpesaPaymentForm(job=job)

    return render(request, 'customers/job_pay_mpesa.html', {
        'form': form,
        'job': job,
    })
