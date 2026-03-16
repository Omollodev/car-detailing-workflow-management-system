"""
Signal handlers for the accounts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_worker_profile(sender, instance, created, **kwargs):
    """
    Create a WorkerProfile when a new worker user is created.
    """
    if created and instance.role == User.Role.WORKER:
        from apps.workers.models import WorkerProfile
        WorkerProfile.objects.get_or_create(user=instance)
