"""
Views for customer and vehicle management.
"""

import logging

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse

from apps.accounts.decorators import manager_required, customer_required
from apps.jobs.forms import CustomerJobBookingForm
from apps.jobs.models import Job, JobService, MpesaStkInitiation

from .models import Customer, Vehicle
from .forms import (
    CustomerForm,
    VehicleForm,
    QuickCustomerVehicleForm,
    CustomerPortalProfileForm,
    CustomerMpesaPaymentForm,
    PaymentMethodSelectionForm,
)
from .mpesa_daraja import (
    extract_stk_result,
    normalize_kenya_msisdn,
    parse_stk_callback_body,
    stk_push,
)

logger = logging.getLogger(__name__)


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
        'mpesa_stk_enabled': bool(getattr(settings, 'MPESA_DARAJA_ENABLED', False)),
    })


@login_required
@customer_required
@require_http_methods(['POST'])
def customer_job_mpesa_stk_initiate_view(request, job_pk):
    """
    Start Safaricom Daraja STK Push for the job balance (customer portal).
    """
    from decimal import ROUND_UP, Decimal

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
        messages.warning(request, 'Payment is not available for this job.')
        return redirect('jobs:detail', pk=job.pk)

    phone_raw = (request.POST.get('stk_phone') or '').strip()
    if not phone_raw:
        messages.error(request, 'Enter the M-Pesa phone number that will receive the prompt.')
        return redirect('customers:job_pay_mpesa', job_pk=job.pk)

    try:
        msisdn = normalize_kenya_msisdn(phone_raw)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('customers:job_pay_mpesa', job_pk=job.pk)

    amount = job.balance_due.quantize(Decimal('1'), rounding=ROUND_UP)
    acc_ref = f'JOB{job.pk}'[:12]

    try:
        resp = stk_push(
            phone_msisdn=msisdn,
            amount=amount,
            account_reference=acc_ref,
            transaction_desc=f'Job {job.pk}',
        )
    except Exception as exc:
        logger.exception('STK push failed for job %s', job.pk)
        messages.error(
            request,
            f'Could not start M-Pesa on your phone. {exc}',
        )
        return redirect('customers:job_pay_mpesa', job_pk=job.pk)

    if str(resp.get('ResponseCode', '1')) != '0':
        msg = (
            resp.get('CustomerMessage')
            or resp.get('errorMessage')
            or resp.get('ResponseDescription')
            or 'M-Pesa could not start this payment.'
        )
        messages.error(request, msg)
        return redirect('customers:job_pay_mpesa', job_pk=job.pk)

    checkout_id = (resp.get('CheckoutRequestID') or '').strip()
    merchant_id = (resp.get('MerchantRequestID') or '').strip()
    if checkout_id:
        MpesaStkInitiation.objects.create(
            job=job,
            checkout_request_id=checkout_id,
            merchant_request_id=merchant_id[:120],
            amount=amount,
            phone=msisdn,
        )

    messages.success(
        request,
        'Check your phone to approve the M-Pesa payment. '
        'Your job balance will update automatically after you complete it.',
    )
    return redirect('jobs:detail', pk=job.pk)


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_stk_callback_view(request):
    """
    Daraja STK callback (no CSRF; must be HTTPS and publicly reachable in production).
    """
    from decimal import Decimal

    data = parse_stk_callback_body(request.body)
    parsed = extract_stk_result(data)
    if not parsed or not parsed.get('checkout_request_id'):
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    checkout_id = parsed['checkout_request_id']
    try:
        initiation = MpesaStkInitiation.objects.select_related('job').get(
            checkout_request_id=checkout_id
        )
    except MpesaStkInitiation.DoesNotExist:
        logger.warning('STK callback: unknown CheckoutRequestID %s', checkout_id)
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    if initiation.status == MpesaStkInitiation.Status.COMPLETED:
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    rc = parsed.get('result_code')
    if rc != 0:
        initiation.status = MpesaStkInitiation.Status.FAILED
        initiation.result_desc = str(parsed.get('result_desc') or '')[:500]
        initiation.save(update_fields=['status', 'result_desc', 'updated_at'])
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    receipt = (parsed.get('mpesa_receipt') or '').strip()
    raw_amount = parsed.get('amount')
    if raw_amount is not None:
        pay_amount = Decimal(str(raw_amount))
    else:
        pay_amount = initiation.amount

    job = initiation.job
    if receipt and job.mpesa_transaction_id == receipt:
        initiation.status = MpesaStkInitiation.Status.COMPLETED
        initiation.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    txn_id = receipt or f'STK-{checkout_id[:20]}'
    job.apply_mpesa_payment(
        pay_amount,
        phone=parsed.get('phone') or initiation.phone,
        transaction_id=txn_id,
        user=None,
    )
    initiation.status = MpesaStkInitiation.Status.COMPLETED
    initiation.result_desc = 'Success'
    initiation.save(update_fields=['status', 'result_desc', 'updated_at'])

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
