"""Notifications admin."""

from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__username', 'title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
