"""Notifications views."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.notifications.models import Notification


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    context = {
        'notifications': notifications,
        'page_title': 'Notifications',
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return JsonResponse({'success': True})


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})
