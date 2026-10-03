"""Sportsbook admin."""

from django.contrib import admin

from apps.sportsbook.models import Country, Event, League, Market, Sport, Team


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'flag']
    search_fields = ['name', 'code']


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ['name', 'sport', 'country', 'is_active', 'is_featured', 'display_order']
    list_filter = ['sport', 'is_active', 'is_featured']
    list_editable = ['is_active', 'is_featured', 'display_order']
    search_fields = ['name', 'sport__name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'sport', 'country']
    list_filter = ['sport']
    search_fields = ['name', 'short_name']


class MarketInline(admin.TabularInline):
    model = Market
    extra = 0
    fields = ['name', 'market_type', 'status', 'is_main_market', 'display_order']
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'home_team', 'away_team', 'league', 'starts_at',
        'status', 'is_featured', 'betting_active',
    ]
    list_filter = ['status', 'league__sport', 'is_featured', 'betting_active']
    list_editable = ['status', 'is_featured', 'betting_active']
    search_fields = ['home_team__name', 'away_team__name', 'league__name']
    date_hierarchy = 'starts_at'
    inlines = [MarketInline]
    raw_id_fields = ['home_team', 'away_team']


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'market_type', 'status', 'is_main_market']
    list_filter = ['status', 'is_main_market', 'market_type']
    search_fields = ['name', 'event__home_team__name', 'event__away_team__name']
    raw_id_fields = ['event']
