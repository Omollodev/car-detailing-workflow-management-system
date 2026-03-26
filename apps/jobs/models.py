"""
Job and JobService models - Core models for the carwash workflow management system.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import json

from .customer_notify import (
    notify_customer_payment,
    notify_customer_services_completed,
)

class Job(models.Model):
    """
    Core model representing a car detailing job.
    
    Tracks the full lifecycle of a job from creation to completion,
    including status transitions, assigned services, worker assignments,
    and timeline events.
    """
    
    class Status(models.TextChoices):
        WAITING = 'waiting', _('Waiting')
        IN_PROGRESS = 'in_progress', _('In Progress')
        AWAITING_EXTRA = 'awaiting_extra', _('Awaiting Extra Services')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    class Priority(models.TextChoices):
        NORMAL = 'normal', _('Normal')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PARTIAL = 'partial', _('Partial Payment')
        PAID = 'paid', _('Paid')
        REFUNDED = 'refunded', _('Refunded')

    class PaymentChannel(models.TextChoices):
        """How payment is recorded; M-Pesa updates from customer portal; cash from manager."""
        UNSPECIFIED = 'unspecified', _('Not set')
        MPESA = 'mpesa', _('M-Pesa')
        CASH = 'cash', _('Cash')
    
    # Relationships
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='jobs',
        verbose_name=_('Customer')
    )
    
    vehicle = models.ForeignKey(
        'customers.Vehicle',
        on_delete=models.PROTECT,
        related_name='jobs',
        verbose_name=_('Vehicle')
    )
    
    assigned_worker = models.ForeignKey(
        'workers.WorkerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_jobs',
        verbose_name=_('Assigned Worker')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_jobs',
        verbose_name=_('Created By')
    )
    
    # Services through model
    services = models.ManyToManyField(
        'services.Service',
        through='JobService',
        related_name='jobs',
        verbose_name=_('Services')
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name=_('Status'),
        db_index=True
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        verbose_name=_('Priority')
    )
    
    # Alert flag for pending extra services
    need_alert = models.BooleanField(
        default=False,
        verbose_name=_('Needs Alert'),
        help_text=_('True if job has pending extra services')
    )
    
    # Instructions and notes
    special_instructions = models.TextField(
        blank=True,
        verbose_name=_('Special Instructions'),
        help_text=_('Special requirements or customer requests')
    )
    
    internal_notes = models.TextField(
        blank=True,
        verbose_name=_('Internal Notes'),
        help_text=_('Notes visible only to staff')
    )
    
    # Pricing
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Estimated Price (KES)')
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total Price (KES)')
    )
    
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Discount (KES)')
    )
    
    # Payment tracking
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_('Payment Status')
    )
    
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Amount Paid (KES)')
    )

    payment_channel = models.CharField(
        max_length=20,
        choices=PaymentChannel.choices,
        default=PaymentChannel.UNSPECIFIED,
        verbose_name=_('Payment channel'),
        help_text=_('M-Pesa when customer pays online; cash when manager records payment'),
    )

    mpesa_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('M-Pesa phone'),
        help_text=_('Phone used for the last M-Pesa payment'),
    )

    mpesa_transaction_id = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('M-Pesa confirmation'),
        help_text=_('MPESA transaction code or reference'),
    )

    # Duration tracking
    estimated_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Duration (minutes)')
    )
    
    actual_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Actual Duration (minutes)')
    )
    
    # Timeline tracking (stored as JSON)
    timeline = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Timeline'),
        help_text=_('History of status changes and events')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Queue number for the day
    queue_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Queue Number'),
        help_text=_('Position in the daily queue')
    )
    
    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assigned_worker', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"Job #{self.id} - {self.vehicle.plate_number} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generate queue number for new jobs
        if not self.pk and not self.queue_number:
            today = timezone.now().date()
            last_job = Job.objects.filter(
                created_at__date=today
            ).order_by('-queue_number').first()
            self.queue_number = (last_job.queue_number + 1) if last_job and last_job.queue_number else 1
        
        # Calculate estimated price and duration from services
        if not self.pk:
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    # ==================== Status Methods ====================
    
    @property
    def status_badge_class(self) -> str:
        """Return Bootstrap badge class for current status."""
        classes = {
            'waiting': 'bg-secondary',
            'in_progress': 'bg-primary',
            'awaiting_extra': 'bg-warning text-dark',
            'completed': 'bg-success',
            'cancelled': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def priority_badge_class(self) -> str:
        """Return Bootstrap badge class for priority."""
        classes = {
            'normal': 'bg-secondary',
            'high': 'bg-warning text-dark',
            'urgent': 'bg-danger',
        }
        return classes.get(self.priority, 'bg-secondary')
    
    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if the job can transition to the specified status.
        
        Status transition rules:
        - waiting -> in_progress, cancelled
        - in_progress -> awaiting_extra, completed, cancelled
        - awaiting_extra -> in_progress, completed
        - completed -> (no transitions)
        - cancelled -> (no transitions)
        """
        allowed_transitions = {
            'waiting': ['in_progress', 'cancelled'],
            'in_progress': ['awaiting_extra', 'completed', 'cancelled'],
            'awaiting_extra': ['in_progress', 'completed'],
            'completed': [],
            'cancelled': [],
        }
        return new_status in allowed_transitions.get(self.status, [])
    
    def can_be_completed(self) -> bool:
        """
        Check if job can be marked as completed.
        Job can only be completed when ALL services are marked as done.
        """
        if not self.can_transition_to('completed'):
            return False
        return not self.has_pending_services()
    
    def get_completion_blockers(self) -> list:
        """
        Return list of reasons why job cannot be completed.
        Useful for displaying error messages to users.
        """
        blockers = []
        
        if not self.can_transition_to('completed'):
            blockers.append(f"Cannot transition from '{self.get_status_display()}' to Completed")
        
        if self.has_pending_services():
            pending_count = self.get_pending_services().count()
            blockers.append(f"{pending_count} service(s) still pending. Mark all services as complete first.")
        
        return blockers
    
    def change_status(self, new_status: str, user=None, notes: str = '') -> bool:
        """
        Change job status with validation and timeline tracking.
        
        Returns True if status was changed successfully, False otherwise.
        """
        if not self.can_transition_to(new_status):
            return False
        
        # Completion requires every line-item service marked done (not only extras)
        if new_status == 'completed':
            if self.has_pending_services():
                return False
        
        old_status = self.status
        self.status = new_status
        
        # Update timestamps
        if new_status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()
        elif new_status == 'completed':
            self.completed_at = timezone.now()
            if self.started_at:
                delta = self.completed_at - self.started_at
                self.actual_duration = int(delta.total_seconds() / 60)
        
        # Update alert flag
        self.update_alert_flag()
        
        # Add timeline event
        self.add_timeline_event(
            event_type='status_change',
            description=f'Status changed from {old_status} to {new_status}',
            user=user,
            notes=notes
        )
        
        self.save()
        if (
            new_status == self.Status.COMPLETED
            and old_status != self.Status.COMPLETED
        ):
            _notify_managers_job_completed(self, user)
        return True
    
    def update_alert_flag(self):
        """Update the need_alert flag based on pending extra services."""
        self.need_alert = self.has_pending_extra_services()
    
    # ==================== Service Methods ====================
    
    def has_pending_extra_services(self) -> bool:
        """Check if job has any incomplete extra (detailing/additional) services."""
        return self.jobservice_set.filter(
            service__category__in=['detailing', 'additional'],
            is_completed=False,
        ).exists()
    
    def has_pending_services(self) -> bool:
        """Check if job has any incomplete services."""
        return self.jobservice_set.filter(is_completed=False).exists()
    
    def get_pending_services(self):
        """Return all incomplete services for this job."""
        return self.jobservice_set.filter(is_completed=False)
    
    def get_completed_services(self):
        """Return all completed services for this job."""
        return self.jobservice_set.filter(is_completed=True)
    
    def get_basic_services(self):
        """Return all basic services for this job (exterior and interior)."""
        return self.jobservice_set.filter(service__category__in=['exterior', 'interior'])
    
    def get_extra_services(self):
        """Return all extra services for this job (detailing and additional)."""
        return self.jobservice_set.filter(service__category__in=['detailing', 'additional'])
    
    def calculate_totals(self):
        """Calculate and update estimated price and duration from services."""
        job_services = self.jobservice_set.all()
        
        self.estimated_price = sum(
            js.service.price for js in job_services
        )
        self.estimated_duration = sum(
            js.service.estimated_duration for js in job_services
        )
        
        # Apply discount
        self.total_price = max(
            self.estimated_price - self.discount,
            Decimal('0.00')
        )
        
        self.save(update_fields=['estimated_price', 'estimated_duration', 'total_price'])
    
    # ==================== Timeline Methods ====================
    
    def add_timeline_event(self, event_type: str, description: str, 
                           user=None, notes: str = ''):
        """Add an event to the job timeline."""
        event = {
            'timestamp': timezone.now().isoformat(),
            'type': event_type,
            'description': description,
            'user': user.username if user else None,
            'user_name': user.get_full_name() if user else None,
            'notes': notes,
        }
        
        if self.timeline is None:
            self.timeline = []
        
        self.timeline.append(event)
    
    def get_timeline(self) -> list:
        """Return the timeline as a list of events."""
        return self.timeline or []
    
    # ==================== Pricing Methods ====================
    
    @property
    def formatted_total_price(self) -> str:
        """Return total price formatted as KES currency."""
        return f"KES {self.total_price:,.2f}"
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance to be paid."""
        return max(self.total_price - self.amount_paid, Decimal('0.00'))
    
    @property
    def is_fully_paid(self) -> bool:
        """Check if job is fully paid."""
        return self.amount_paid >= self.total_price

    def apply_mpesa_payment(
        self,
        amount: Decimal,
        *,
        phone: str = '',
        transaction_id: str = '',
        user=None,
    ) -> None:
        """
        Add an M-Pesa amount from the customer portal and sync payment_status.
        Caps amount_paid at total_price. Records timeline event.
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            return
        balance = max(self.total_price - self.amount_paid, Decimal('0.00'))
        applied = min(amount, balance)
        if applied <= 0:
            return
        self.amount_paid = self.amount_paid + applied
        if self.amount_paid >= self.total_price:
            self.payment_status = self.PaymentStatus.PAID
            self.amount_paid = self.total_price
        else:
            self.payment_status = self.PaymentStatus.PARTIAL
        self.payment_channel = self.PaymentChannel.MPESA
        if phone:
            self.mpesa_phone = phone.strip()[:20]
        if transaction_id:
            self.mpesa_transaction_id = transaction_id.strip()[:64]
        self.add_timeline_event(
            event_type='payment_mpesa',
            description=(
                f'M-Pesa payment recorded: KES {applied} '
                f'(balance KES {self.balance_due})'
            ),
            user=user,
            notes=transaction_id or phone or '',
        )
        self.save(
            update_fields=[
                'amount_paid',
                'payment_status',
                'payment_channel',
                'mpesa_phone',
                'mpesa_transaction_id',
                'timeline',
                'updated_at',
            ]
        )
        notify_customer_payment(self, applied, "M-Pesa")

    def apply_cash_payment(
        self,
        amount: Decimal,
        *,
        payment_status: str = 'paid',
        user=None,
        notes: str = '',
    ) -> None:
        """
        Record a cash payment from the manager and update payment_status.
        Caps amount_paid at total_price. Records timeline event.
        """
        amount = Decimal(str(amount))
        if amount <= 0:
            return
        balance = max(self.total_price - self.amount_paid, Decimal('0.00'))
        applied = min(amount, balance)
        if applied <= 0:
            return
        self.amount_paid = self.amount_paid + applied
        
        # Set payment status based on whether balance is fully covered
        if self.amount_paid >= self.total_price:
            self.payment_status = self.PaymentStatus.PAID
            self.amount_paid = self.total_price
        else:
            self.payment_status = payment_status or self.PaymentStatus.PARTIAL
        
        self.payment_channel = self.PaymentChannel.CASH
        
        self.add_timeline_event(
            event_type='payment_cash',
            description=(
                f'Cash payment recorded: KES {applied} '
                f'(Balance: KES {self.balance_due})'
            ),
            user=user,
            notes=notes,
        )
        self.save(
            update_fields=[
                'amount_paid',
                'payment_status',
                'payment_channel',
                'timeline',
                'updated_at',
            ]
        )
        notify_customer_payment(self, applied, "cash")

    # ==================== Duration Methods ====================
    
    @property
    def formatted_estimated_duration(self) -> str:
        """Return estimated duration formatted as hours:minutes."""
        if self.estimated_duration >= 60:
            hours = self.estimated_duration // 60
            minutes = self.estimated_duration % 60
            if minutes:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{self.estimated_duration}m"
    
    @property
    def formatted_actual_duration(self) -> str:
        """Return actual duration formatted as hours:minutes."""
        if not self.actual_duration:
            return "-"
        if self.actual_duration >= 60:
            hours = self.actual_duration // 60
            minutes = self.actual_duration % 60
            if minutes:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{self.actual_duration}m"
    
    # ==================== Class Methods ====================
    
    @classmethod
    def get_next_waiting_job(cls):
        """Get the next job in the waiting queue (FIFO)."""
        return cls.objects.filter(
            status=cls.Status.WAITING
        ).order_by('created_at').first()
    
    @classmethod
    def get_jobs_by_status(cls, status: str):
        """Get all jobs with the specified status."""
        return cls.objects.filter(status=status).order_by('created_at')
    
    @classmethod
    def get_todays_jobs(cls):
        """Get all jobs created today."""
        today = timezone.now().date()
        return cls.objects.filter(created_at__date=today)
    
    @classmethod
    def get_active_jobs(cls):
        """Get all non-completed, non-cancelled jobs."""
        return cls.objects.exclude(
            status__in=[cls.Status.COMPLETED, cls.Status.CANCELLED]
        )
    
    @classmethod
    def get_jobs_needing_alert(cls):
        """Get all jobs with the need_alert flag set."""
        return cls.objects.filter(need_alert=True)


class JobService(models.Model):
    """
    Through model for Job-Service relationship.
    
    Tracks completion status and details for each service in a job.
    """
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        verbose_name=_('Job')
    )
    
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT,
        verbose_name=_('Service')
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed')
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed At')
    )
    
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_services',
        verbose_name=_('Completed By')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Notes about this service for this job')
    )
    
    photo = models.ImageField(
        upload_to='job_service_photos/',
        blank=True,
        null=True,
        verbose_name=_('Photo'),
        help_text=_('Photo evidence of completed service')
    )
    
    # Price override for special pricing
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Price Override'),
        help_text=_('Override standard service price')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Job Service')
        verbose_name_plural = _('Job Services')
        unique_together = ['job', 'service']
        ordering = ['service__category', 'service__display_order']
    
    def __str__(self) -> str:
        status = "Done" if self.is_completed else "Pending"
        return f"{self.job} - {self.service.name} ({status})"
    
    @property
    def effective_price(self) -> Decimal:
        """Return the effective price (override or standard)."""
        if self.price_override is not None:
            return self.price_override
        return self.service.price
    
    def mark_complete(self, user=None):
        """Mark this service as completed."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()
        
        # Update job alert flag
        self.job.update_alert_flag()
        self.job.save(update_fields=['need_alert'])
        
        # Add timeline event
        self.job.add_timeline_event(
            event_type='service_completed',
            description=f'Service "{self.service.name}" marked as completed',
            user=user
        )
        self.job.save(update_fields=['timeline'])

        # Notify customer once all services on the job are done.
        if not self.job.has_pending_services():
            notify_customer_services_completed(self.job)
    
    def mark_incomplete(self, user=None):
        """Mark this service as incomplete (undo completion)."""
        self.is_completed = False
        self.completed_at = None
        self.completed_by = None
        self.save()
        
        # Update job alert flag
        self.job.update_alert_flag()
        self.job.save(update_fields=['need_alert'])


class MpesaStkInitiation(models.Model):
    """
    Tracks a Daraja STK Push request until the callback confirms success/failure.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    job = models.ForeignKey(
        'Job',
        on_delete=models.CASCADE,
        related_name='mpesa_stk_requests',
    )
    checkout_request_id = models.CharField(
        max_length=120,
        unique=True,
        db_index=True,
    )
    merchant_request_id = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    result_desc = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('M-Pesa STK initiation')
        verbose_name_plural = _('M-Pesa STK initiations')

    def __str__(self) -> str:
        return f"STK {self.checkout_request_id[:20]}… → Job #{self.job_id}"


def _notify_managers_job_completed(job: 'Job', completed_by=None) -> None:
    """
    Notify all active admins/managers when a job moves to completed.
    Imports are local to avoid circular dependencies.
    """
    from django.contrib.auth import get_user_model
    from apps.notifications.models import Notification

    User = get_user_model()
    recipients = User.objects.filter(
        role__in=[User.Role.ADMIN, User.Role.MANAGER],
        is_active=True,
    )
    who = (
        completed_by.get_full_name() or completed_by.username
        if completed_by
        else 'Staff'
    )
    for recipient in recipients:
        Notification.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.JOB_COMPLETED,
            title='Job completed',
            message=(
                f'{who} marked Job #{job.id} ({job.vehicle.plate_number}) '
                f'for {job.customer.name} as completed.'
            ),
            job=job,
        )
