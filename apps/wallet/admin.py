"""Wallet admin."""

from django.contrib import admin

from apps.wallet.models import Transaction, Wallet


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = [
        'id', 'transaction_type', 'amount', 'balance_before',
        'balance_after', 'status', 'created_at',
    ]
    can_delete = False
    max_num = 10


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'bonus_balance', 'is_frozen', 'updated_at']
    list_filter = ['currency', 'is_frozen']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'wallet', 'transaction_type', 'amount',
        'balance_after', 'status', 'created_at',
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['wallet__user__username', 'reference', 'provider_transaction_id']
    readonly_fields = [
        'id', 'wallet', 'transaction_type', 'amount',
        'balance_before', 'balance_after', 'created_at',
    ]
    date_hierarchy = 'created_at'
    list_select_related = ['wallet__user']
