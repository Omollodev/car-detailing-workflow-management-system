"""
Custom decorators for role-based access control.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """
    Decorator that requires the user to have admin role.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to continue.')
            return redirect('accounts:login')
        
        if not request.user.is_admin:
            messages.error(request, 'Administrator access required.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def manager_required(view_func):
    """
    Decorator that requires the user to have manager role or higher.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to continue.')
            return redirect('accounts:login')
        
        if not request.user.is_manager:
            messages.error(request, 'Manager access required.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def worker_required(view_func):
    """
    Decorator that requires the user to be a worker (or manager/admin).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to continue.')
            return redirect('accounts:login')
        
        if not (request.user.is_worker or request.user.is_manager):
            messages.error(request, 'Worker access required.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def customer_required(view_func):
    """
    Decorator for views that only customer portal users may access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to continue.')
            return redirect('accounts:login')

        if not getattr(request.user, 'is_customer', False):
            messages.error(request, 'This area is for customers only.')
            return redirect('dashboard:index')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ajax_login_required(view_func):
    """
    Decorator for AJAX views that returns JSON error if not authenticated.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
