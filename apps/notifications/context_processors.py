"""
Context processors for notifications app.
"""

from .models import Notification


def unread_notifications_count(request):
    """
    Add unread notifications count to all template contexts.
    """
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': Notification.get_unread_count(request.user)
        }
    return {'unread_notifications_count': 0}
