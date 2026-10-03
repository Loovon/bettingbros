"""Promotions admin."""

from django.contrib import admin

from apps.promotions.models import Promotion, UserPromotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'promotion_type', 'is_active', 'is_featured',
        'priority', 'start_date', 'end_date',
    ]
    list_filter = ['promotion_type', 'is_active', 'is_featured']
    list_editable = ['is_active', 'is_featured', 'priority']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'


@admin.register(UserPromotion)
class UserPromotionAdmin(admin.ModelAdmin):
    list_display = ['user', 'promotion', 'status', 'claimed_at', 'bonus_credited']
    list_filter = ['status']
    search_fields = ['user__username', 'promotion__title']
    readonly_fields = ['claimed_at']
