"""Casino admin."""

from django.contrib import admin

from apps.casino.models import CasinoGame, GameCategory, GameProvider


@admin.register(GameProvider)
class GameProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CasinoGame)
class CasinoGameAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'category', 'rtp', 'status',
        'is_featured', 'is_new', 'play_count',
    ]
    list_filter = ['status', 'category', 'provider', 'is_featured', 'is_new']
    list_editable = ['status', 'is_featured', 'is_new']
    search_fields = ['name', 'provider__name', 'external_game_id']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['play_count', 'created_at']
