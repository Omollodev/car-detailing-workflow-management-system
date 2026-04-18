"""
URL patterns for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path(
        'verification-pending/',
        views.verification_pending_view,
        name='verification_pending',
    ),
    path(
        'resend-verification/',
        views.resend_verification_email_view,
        name='resend_verification',
    ),
    path('logout/', views.logout_view, name='logout'),
    path('register/customer/', views.customer_register_view, name='customer_register'),
    path(
        'verify-email/<uidb64>/<token>/',
        views.verify_email_view,
        name='verify_email',
    ),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # User management (admin only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active_view, name='user_toggle_active'),
]
