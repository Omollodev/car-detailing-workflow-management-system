"""
Custom User model with role-based permissions for the Car Detailing system.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Extended User model with additional fields for the car detailing business.
    
    Roles:
    - admin: Full system access, can manage users and settings
    - manager: Can manage jobs, workers, customers, and view reports
    - worker: Can view assigned jobs and update job status (created by admin/manager)
    - customer: Self-registered portal user; books services and manages own profile/vehicles
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        MANAGER = 'manager', _('Manager')
        WORKER = 'worker', _('Worker')
        CUSTOMER = 'customer', _('Customer')
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
        verbose_name=_('Role'),
        help_text=_('User role determines access permissions')
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number'),
        help_text=_('Contact phone number')
    )
    
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name=_('Profile Picture')
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date of Birth')
    )
    
    address = models.TextField(
        blank=True,
        verbose_name=_('Address')
    )
    
    is_active_worker = models.BooleanField(
        default=True,
        verbose_name=_('Active Worker'),
        help_text=_('Designates whether this worker is currently active')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']
    
    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_manager(self) -> bool:
        """Check if user has manager role or higher."""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def is_worker(self) -> bool:
        """Check if user has worker role."""
        return self.role == self.Role.WORKER
    
    @property
    def is_customer(self) -> bool:
        """Check if user is a self-service customer portal user."""
        return self.role == self.Role.CUSTOMER
    
    def can_manage_jobs(self) -> bool:
        """Check if user can create/edit jobs."""
        return self.is_manager or self.is_admin
    
    def can_manage_workers(self) -> bool:
        """Check if user can manage worker assignments."""
        return self.is_manager or self.is_admin
    
    def can_manage_customers(self) -> bool:
        """Check if user can manage customer records."""
        return self.is_manager or self.is_admin
    
    def can_view_reports(self) -> bool:
        """Check if user can view business reports."""
        return self.is_manager or self.is_admin
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.is_admin
