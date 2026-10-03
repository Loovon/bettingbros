"""Odds admin."""

from django.contrib import admin

from apps.odds.models import Odd, OddsHistory


class OddsHistoryInline(admin.TabularInline):
    model = OddsHistory
    extra = 0
    readonly_fields = ['decimal_odds', 'recorded_at']
    can_delete = False


@admin.register(Odd)
class OddAdmin(admin.ModelAdmin):
    list_display = ['name', 'market', 'decimal_odds', 'status', 'result', 'display_order']
    list_filter = ['status', 'result']
    search_fields = ['name', 'market__name', 'market__event__home_team__name']
    list_editable = ['decimal_odds', 'status']
    raw_id_fields = ['market']
    inlines = [OddsHistoryInline]
