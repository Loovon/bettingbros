"""Payments admin."""

from django.contrib import admin

from apps.payments.models import PaymentMethod, PaymentProviderConfig


@admin.register(PaymentProviderConfig)
class PaymentProviderConfigAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider_code', 'is_active',
        'supports_deposits', 'supports_withdrawals', 'display_order',
    ]
    list_editable = ['is_active', 'display_order']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'method_type', 'provider', 'display_name', 'is_default', 'is_active']
    list_filter = ['method_type', 'provider', 'is_active']
    search_fields = ['user__username', 'display_name']
    readonly_fields = ['provider_token']  # Don't expose tokens in list view
