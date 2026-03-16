"""
Notification model for user notifications.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """
    User notification for job updates, assignments, and alerts.
    """
    
    class NotificationType(models.TextChoices):
        JOB_ASSIGNED = 'job_assigned', _('Job Assigned')
        JOB_UPDATED = 'job_updated', _('Job Updated')
        JOB_COMPLETED = 'job_completed', _('Job Completed')
        EXTRA_SERVICE = 'extra_service', _('Extra Service Added')
        ALERT = 'alert', _('Alert')
        INFO = 'info', _('Information')
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name=_('Type')
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title')
    )
    
    message = models.TextField(
        verbose_name=_('Message')
    )
    
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('Related Job')
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Read')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self) -> str:
        status = "Read" if self.is_read else "Unread"
        return f"{self.title} ({status})"
    
    @property
    def icon_class(self) -> str:
        """Return Bootstrap icon class for notification type."""
        icons = {
            'job_assigned': 'bi-person-check',
            'job_updated': 'bi-arrow-repeat',
            'job_completed': 'bi-check-circle',
            'extra_service': 'bi-plus-circle',
            'alert': 'bi-exclamation-triangle',
            'info': 'bi-info-circle',
        }
        return icons.get(self.notification_type, 'bi-bell')
    
    @property
    def badge_class(self) -> str:
        """Return Bootstrap badge class for notification type."""
        badges = {
            'job_assigned': 'bg-primary',
            'job_updated': 'bg-info',
            'job_completed': 'bg-success',
            'extra_service': 'bg-warning text-dark',
            'alert': 'bg-danger',
            'info': 'bg-secondary',
        }
        return badges.get(self.notification_type, 'bg-secondary')
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, job=None):
        """Create and return a new notification."""
        return cls.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            job=job
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user."""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def get_recent_notifications(cls, user, limit=10):
        """Get recent notifications for a user."""
        return cls.objects.filter(recipient=user)[:limit]
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user."""
        from django.utils import timezone
        cls.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
