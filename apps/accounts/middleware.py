"""
Custom middleware for role-based access control.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control on certain URL patterns.
    """
    
    # URLs that require specific roles
    MANAGER_REQUIRED_PATHS = [
        '/workers/manage/',
        '/reports/',
    ]
    
    ADMIN_REQUIRED_PATHS = [
        '/accounts/users/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            path = request.path
            
            # Check admin-required paths
            for admin_path in self.ADMIN_REQUIRED_PATHS:
                if path.startswith(admin_path):
                    if not request.user.is_admin:
                        messages.error(request, 'You do not have permission to access this page.')
                        return redirect('dashboard:index')
            
            # Check manager-required paths
            for manager_path in self.MANAGER_REQUIRED_PATHS:
                if path.startswith(manager_path):
                    if not request.user.is_manager:
                        messages.error(request, 'You do not have permission to access this page.')
                        return redirect('dashboard:index')
        
        response = self.get_response(request)
        return response
