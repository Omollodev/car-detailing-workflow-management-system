"""
Service model for managing the service catalog.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Service(models.Model):
    """
    Represents a service offered by the car detailing business.
    
    Services are categorized and have pricing and duration information.
    """
    
    class Category(models.TextChoices):
        EXTERIOR = 'exterior', _('Exterior')
        INTERIOR = 'interior', _('Interior')
        DETAILING = 'detailing', _('Detailing')
        ADDITIONAL = 'additional', _('Additional Services')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Service Name'),
        help_text=_('Name of the service')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of the service')
    )
    
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.EXTERIOR,
        verbose_name=_('Category'),
        help_text=_('Service category')
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Price (KES)'),
        help_text=_('Service price in Kenyan Shillings')
    )
    
    estimated_duration = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Estimated Duration (minutes)'),
        help_text=_('Estimated time to complete the service')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Inactive services are not available for new jobs')
    )
    
    requires_special_equipment = models.BooleanField(
        default=False,
        verbose_name=_('Requires Special Equipment'),
        help_text=_('Whether this service needs special tools or equipment')
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Display Order'),
        help_text=_('Order in which service appears in lists')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['display_order', 'category', 'name']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_display()}) - KES {self.price}"
    
    @property
    def formatted_price(self) -> str:
        """Return price formatted as KES currency."""
        return f"KES {self.price:,.2f}"
    
    @property
    def formatted_duration(self) -> str:
        """Return duration formatted as hours:minutes or just minutes."""
        if self.estimated_duration >= 60:
            hours = self.estimated_duration // 60
            minutes = self.estimated_duration % 60
            if minutes:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{self.estimated_duration}m"
    
    @classmethod
    def get_all_active_services(cls):
        """Return all active services ordered by category and name."""
        return cls.objects.filter(is_active=True).order_by('category', 'display_order', 'name')
