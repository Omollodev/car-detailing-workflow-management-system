"""
Signal handlers for the jobs app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Job, JobService


@receiver(post_save, sender=Job)
def job_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Job model."""
    if created:
        instance.add_timeline_event(
            event_type='created',
            description='Job created',
            user=instance.created_by,
        )
        instance.save(update_fields=['timeline'])


@receiver(post_save, sender=JobService)
def job_service_post_save(sender, instance, created, **kwargs):
    """Update job totals when a JobService is added or modified."""
    instance.job.calculate_totals()
    instance.job.update_alert_flag()
    instance.job.save(update_fields=['need_alert'])


@receiver(post_delete, sender=JobService)
def job_service_post_delete(sender, instance, **kwargs):
    """Update job totals when a JobService is removed."""
    try:
        instance.job.calculate_totals()
        instance.job.update_alert_flag()
        instance.job.save(update_fields=['need_alert'])
    except Job.DoesNotExist:
        pass
