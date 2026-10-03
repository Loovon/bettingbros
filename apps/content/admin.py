"""Content admin."""

from django.contrib import admin

from apps.content.models import Announcement, Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'is_active', 'priority', 'start_date', 'end_date']
    list_filter = ['placement', 'is_active']
    list_editable = ['is_active', 'priority']
    search_fields = ['title']
    date_hierarchy = 'start_date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['message', 'announcement_type', 'is_active', 'priority', 'start_date', 'end_date']
    list_filter = ['announcement_type', 'is_active']
    list_editable = ['is_active']
