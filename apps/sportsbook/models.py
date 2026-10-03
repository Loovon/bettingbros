"""
Sportsbook models — Sports, Leagues, Teams, Events, Markets.
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Sport(models.Model):
    """A top-level sport (Football, Basketball, Tennis …)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='CSS icon class or emoji')
    image = models.ImageField(upload_to='sports/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Sport')
        verbose_name_plural = _('Sports')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True, help_text='ISO 3166-1 alpha-2')
    flag = models.CharField(max_length=10, blank=True, help_text='Unicode flag emoji')

    class Meta:
        ordering = ['name']
        verbose_name_plural = _('Countries')

    def __str__(self) -> str:
        return self.name


class League(models.Model):
    """A competition league or tournament."""

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='leagues')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    logo = models.ImageField(upload_to='leagues/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    external_id = models.CharField(max_length=100, blank=True, db_index=True,
                                   help_text='ID from external odds/data provider')

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('League')
        verbose_name_plural = _('Leagues')

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f'{self.sport.name}-{self.name}')
            self.slug = base
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.sport.name} — {self.name}'


class Team(models.Model):
    """A team or competitor."""

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10, blank=True)
    logo = models.ImageField(upload_to='teams/', null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    external_id = models.CharField(max_length=100, blank=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')
        indexes = [models.Index(fields=['sport', 'name'])]

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    """
    A sporting event (match, race, game).
    An event belongs to a league and has two competitors (home/away)
    plus a set of Markets.
    """

    class EventStatus(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled')
        LIVE = 'live', _('Live')
        FINISHED = 'finished', _('Finished')
        POSTPONED = 'postponed', _('Postponed')
        CANCELLED = 'cancelled', _('Cancelled')
        SUSPENDED = 'suspended', _('Suspended')

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='events')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_events')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_events')

    slug = models.SlugField(max_length=300, blank=True, db_index=True)
    starts_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.SCHEDULED,
        db_index=True,
    )

    # Live score
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    match_time = models.CharField(max_length=20, blank=True, help_text="e.g. '45+2' or '2nd Half'")

    # Flags
    is_featured = models.BooleanField(default=False, db_index=True)
    is_live_streaming = models.BooleanField(default=False)
    betting_active = models.BooleanField(default=True)

    external_id = models.CharField(max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['starts_at']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        indexes = [
            models.Index(fields=['status', 'starts_at']),
            models.Index(fields=['league', 'starts_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.home_team.name}-vs-{self.away_team.name}-{self.starts_at.date()}')
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.home_team} vs {self.away_team} ({self.starts_at:%Y-%m-%d %H:%M})'

    @property
    def is_live(self) -> bool:
        return self.status == self.EventStatus.LIVE

    @property
    def score_display(self) -> str:
        if self.home_score is not None and self.away_score is not None:
            return f'{self.home_score} - {self.away_score}'
        return '-'


class Market(models.Model):
    """
    A betting market within an event (e.g. 'Match Result', 'Both Teams to Score').
    """

    class MarketStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        SUSPENDED = 'suspended', _('Suspended')
        CLOSED = 'closed', _('Closed')
        SETTLED = 'settled', _('Settled')

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='markets')
    name = models.CharField(max_length=200)
    market_type = models.CharField(max_length=100, db_index=True,
                                   help_text='e.g. match_winner, both_teams_score, over_under')
    status = models.CharField(max_length=20, choices=MarketStatus.choices, default=MarketStatus.OPEN)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_main_market = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Market')
        verbose_name_plural = _('Markets')
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['event', 'is_main_market']),
        ]

    def __str__(self) -> str:
        return f'{self.event} — {self.name}'
