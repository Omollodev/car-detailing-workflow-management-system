"""
Views for user authentication and account management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from apps.customers.models import Customer

from .forms import (
    LoginForm,
    UserRegistrationForm,
    UserUpdateForm,
    UserAdminForm,
    CustomerRegistrationForm,
)
from .decorators import admin_required
from .models import User


def customer_register_view(request):
    """
    Public registration for customer portal accounts only.
    """
    if request.user.is_authenticated:
        if request.user.is_customer:
            return redirect('customers:portal')
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            name = f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}".strip()
            Customer.objects.create(
                user=user,
                name=name or user.username,
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                business_name=form.cleaned_data.get('business_name', ''),
                address=form.cleaned_data.get('address', ''),
            )
            login(request, user)
            messages.success(request, 'Welcome! Your customer account is ready.')
            return redirect('customers:portal')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/customer_register.html', {'form': form})


def login_view(request):
    """
    Handle user login.
    """
    if request.user.is_authenticated:
        if request.user.is_customer:
            return redirect('customers:portal')
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Handle remember me
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')

            if user.is_customer:
                return redirect('customers:portal')

            # Redirect to next page or staff dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Display and edit user profile.
    """
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@admin_required
def user_list_view(request):
    """
    List all users (admin only).
    """
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_create_view(request):
    """
    Create a new user (admin only).
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create User',
        'button_text': 'Create User',
    })


@admin_required
def user_edit_view(request, pk):
    """
    Edit a user (admin only).
    """
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserAdminForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': f'Edit User: {user.username}',
        'button_text': 'Save Changes',
        'user_obj': user,
    })


@admin_required
@require_http_methods(["POST"])
def user_toggle_active_view(request, pk):
    """
    Toggle user active status (admin only).
    """
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        return JsonResponse({
            'success': False,
            'error': 'Cannot deactivate your own account'
        })
    
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
    })


@login_required
def change_password_view(request):
    """
    Allow user to change their password.
    """
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            if request.user.is_customer:
                return redirect('customers:portal')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Add Bootstrap classes
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    
    return render(request, 'accounts/change_password.html', {'form': form})
