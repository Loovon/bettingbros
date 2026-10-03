"""
Casino models — Providers, Game Categories, Games.
Provider abstraction allows adding game vendors without touching UI logic.
"""

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class GameProvider(models.Model):
    """An external casino game provider (e.g. Evolution, NetEnt, Pragmatic Play)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    logo = models.ImageField(upload_to='casino/providers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    integration_key = models.CharField(max_length=200, blank=True,
                                       help_text='Provider API identifier — keep private')

    class Meta:
        ordering = ['name']
        verbose_name = _('Game Provider')
        verbose_name_plural = _('Game Providers')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class GameCategory(models.Model):
    """A category for casino games (Slots, Table Games, Live Casino …)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='casino/categories/', null=True, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Game Category')
        verbose_name_plural = _('Game Categories')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class CasinoGame(models.Model):
    """A casino game available on the platform."""

    class GameStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Maintenance')
        COMING_SOON = 'coming_soon', _('Coming Soon')
        DISABLED = 'disabled', _('Disabled')

    provider = models.ForeignKey(GameProvider, on_delete=models.CASCADE, related_name='games')
    category = models.ForeignKey(GameCategory, on_delete=models.CASCADE, related_name='games')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='casino/games/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='casino/games/thumbnails/', null=True, blank=True)
    rtp = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Return to player percentage (e.g. 96.50)',
    )
    min_bet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_bet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=GameStatus.choices, default=GameStatus.ACTIVE)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_new = models.BooleanField(default=False, db_index=True)
    has_demo = models.BooleanField(default=False)
    external_game_id = models.CharField(max_length=200, blank=True, db_index=True,
                                        help_text="Provider's game identifier for launch URLs")
    tags = models.CharField(max_length=300, blank=True, help_text='Comma-separated tags')
    play_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-play_count', 'name']
        verbose_name = _('Casino Game')
        verbose_name_plural = _('Casino Games')
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.provider.name}-{self.name}')
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.name} ({self.provider.name})'
