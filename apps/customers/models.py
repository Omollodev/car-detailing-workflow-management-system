"""
Customer and Vehicle models for the Car Detailing system.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Customer(models.Model):
    """
    Represents a customer of the car detailing business.
    
    Tracks customer contact information, service preferences,
    and loyalty metrics.
    """
    
    name = models.CharField(
        max_length=200,
        verbose_name=_('Full Name'),
        help_text=_('Customer full name')
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number'),
        help_text=_('Primary contact number')
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Secondary Phone'),
        help_text=_('Alternative contact number')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email Address')
    )
    
    address = models.TextField(
        blank=True,
        verbose_name=_('Address'),
        help_text=_('Customer address for records')
    )
    
    service_preferences = models.TextField(
        blank=True,
        verbose_name=_('Service Preferences'),
        help_text=_('Customer preferences and special requirements')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about this customer')
    )
    
    # Loyalty tracking
    total_visits = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Visits'),
        help_text=_('Number of times customer has used services')
    )
    
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total Spent (KES)'),
        help_text=_('Total amount spent by customer')
    )
    
    is_vip = models.BooleanField(
        default=False,
        verbose_name=_('VIP Customer'),
        help_text=_('Mark as VIP for priority service')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Inactive customers are hidden from search')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
    
    @property
    def formatted_total_spent(self) -> str:
        """Return total spent formatted as KES currency."""
        return f"KES {self.total_spent:,.2f}"
    
    def get_vehicles(self):
        """Return all vehicles belonging to this customer."""
        return self.vehicles.all()
    
    def get_active_jobs(self):
        """Return all active (non-completed, non-cancelled) jobs."""
        return self.jobs.exclude(status__in=['completed', 'cancelled'])
    
    def get_completed_jobs(self):
        """Return all completed jobs."""
        return self.jobs.filter(status='completed')
    
    def update_loyalty_stats(self):
        """Update total visits and total spent from completed jobs."""
        completed_jobs = self.get_completed_jobs()
        self.total_visits = completed_jobs.count()
        self.total_spent = completed_jobs.aggregate(
            total=models.Sum('total_price')
        )['total'] or Decimal('0.00')
        self.save(update_fields=['total_visits', 'total_spent'])


class Vehicle(models.Model):
    """
    Represents a vehicle belonging to a customer.
    
    Tracks vehicle details and service history.
    """
    
    class VehicleType(models.TextChoices):
        SPORTS_CAR = 'sports_car', _('Sports Car')
        SEDAN = 'sedan', _('Sedan')
        LUXURY_CAR = 'luxury_car', _('Luxury Car')
        SUV = 'suv', _('SUV')
        HATCHBACK = 'hatchback', _('Hatchback')
        PICKUP = 'pickup', _('Pickup/Truck')
        ELECTRIC_CAR = 'electric_car', _('Electric Car')
        VAN = 'van', _('Van/Minibus')
        MOTORCYCLE = 'motorcycle', _('Motorcycle')
        OTHER = 'other', _('Other')
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name=_('Owner')
    )
    
    plate_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Plate Number'),
        help_text=_('Vehicle registration plate number')
    )
    
    make = models.CharField(
        max_length=50,
        verbose_name=_('Make'),
        help_text=_('Vehicle manufacturer (e.g., Toyota, Honda)')
    )
    
    model = models.CharField(
        max_length=50,
        verbose_name=_('Model'),
        help_text=_('Vehicle model (e.g., Corolla, Civic)')
    )
    
    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Year'),
        help_text=_('Year of manufacture')
    )
    
    color = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_('Color')
    )
    
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        default=VehicleType.SEDAN,
        verbose_name=_('Vehicle Type')
    )
    
    mileage = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Mileage (km)'),
        help_text=_('Current odometer reading')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Special notes about this vehicle')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Inactive vehicles are hidden from search')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Vehicle')
        verbose_name_plural = _('Vehicles')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        year_str = f" ({self.year})" if self.year else ""
        return f"{self.plate_number} - {self.make} {self.model}{year_str}"
    
    @property
    def full_description(self) -> str:
        """Return full vehicle description."""
        parts = [self.make, self.model]
        if self.year:
            parts.append(f"({self.year})")
        if self.color:
            parts.append(f"- {self.color}")
        return " ".join(parts)
    
    def get_service_history(self):
        """Return all completed jobs for this vehicle."""
        return self.jobs.filter(status='completed').order_by('-completed_at')
    
    def get_last_service_date(self):
        """Return the date of the last completed service."""
        last_job = self.get_service_history().first()
        return last_job.completed_at if last_job else None
