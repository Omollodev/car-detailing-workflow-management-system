"""
Views for notification management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .models import Notification


@login_required
def notification_list_view(request):
    """
    List all notifications for the current user.
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    
    unread_count = Notification.get_unread_count(request.user)
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_http_methods(["POST"])
def notification_mark_read_view(request, pk):
    """
    Mark a notification as read.
    """
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'unread_count': Notification.get_unread_count(request.user)
        })
    
    # Redirect to job if notification has one
    if notification.job:
        return redirect('jobs:detail', pk=notification.job.pk)
    
    return redirect('notifications:list')


@login_required
@require_http_methods(["POST"])
def notification_mark_all_read_view(request):
    """
    Mark all notifications as read.
    """
    Notification.mark_all_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'unread_count': 0
        })
    
    return redirect('notifications:list')


@login_required
def api_notifications(request):
    """
    API endpoint for notifications (AJAX polling).
    """
    notifications = Notification.get_recent_notifications(request.user, limit=10)
    
    data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'job_id': n.job_id,
        'is_read': n.is_read,
        'icon_class': n.icon_class,
        'badge_class': n.badge_class,
        'created_at': n.created_at.isoformat(),
    } for n in notifications]
    
    return JsonResponse({
        'notifications': data,
        'unread_count': Notification.get_unread_count(request.user),
    })
