"""Bets admin."""

from django.contrib import admin

from apps.bets.models import Bet, BetSelection


class BetSelectionInline(admin.TabularInline):
    model = BetSelection
    extra = 0
    readonly_fields = ['odd', 'odds_at_placement', 'selection_name', 'event_name', 'market_name', 'result']
    can_delete = False


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'bet_type', 'stake', 'total_odds',
        'potential_return', 'actual_return', 'status', 'placed_at',
    ]
    list_filter = ['status', 'bet_type', 'placed_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'id', 'user', 'stake', 'total_odds', 'potential_return',
        'ip_address', 'placed_at',
    ]
    date_hierarchy = 'placed_at'
    inlines = [BetSelectionInline]
    list_select_related = ['user']
