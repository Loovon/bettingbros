"""Accounts admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import ResponsibleGamblingSettings, User


class ResponsibleGamblingInline(admin.StackedInline):
    model = ResponsibleGamblingSettings
    can_delete = False
    verbose_name_plural = 'Responsible Gambling Settings'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ResponsibleGamblingInline]
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'account_status', 'is_email_verified', 'is_age_verified',
        'date_joined', 'is_active',
    ]
    list_filter = ['account_status', 'is_email_verified', 'is_age_verified', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Platform Info', {
            'fields': (
                'date_of_birth', 'phone_number', 'country', 'currency',
                'avatar', 'account_status',
            ),
        }),
        ('Verification', {
            'fields': ('is_email_verified', 'is_identity_verified', 'is_age_verified'),
        }),
        ('Preferences', {
            'fields': ('odds_format', 'receive_promotions', 'receive_bet_updates'),
        }),
    )
