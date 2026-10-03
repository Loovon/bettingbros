"""
Odds models — individual selections/prices within a market, and odds history.
"""

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.sportsbook.models import Market


class Odd(models.Model):
    """
    A single odds price for a selection within a market.
    e.g. Manchester United to win at odds of 2.10.
    """

    class OddStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        RESULTED = 'resulted', _('Resulted')

    class Result(models.TextChoices):
        WIN = 'win', _('Win')
        LOSE = 'lose', _('Lose')
        VOID = 'void', _('Void')
        PENDING = 'pending', _('Pending')

    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='odds')
    name = models.CharField(max_length=200, help_text='Selection name, e.g. "Manchester United", "Over 2.5"')
    decimal_odds = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text='Decimal representation, e.g. 2.100',
    )
    handicap = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=OddStatus.choices, default=OddStatus.ACTIVE)
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING)
    display_order = models.PositiveSmallIntegerField(default=0)
    external_id = models.CharField(max_length=100, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Odd')
        verbose_name_plural = _('Odds')
        indexes = [
            models.Index(fields=['market', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.market} | {self.name} @ {self.decimal_odds}'

    @property
    def is_active(self) -> bool:
        return self.status == self.OddStatus.ACTIVE

    def fractional_display(self) -> str:
        """Convert decimal odds to fractional string for display."""
        decimal = float(self.decimal_odds)
        numerator = decimal - 1
        # Simplify to nearest common fraction — approximate
        from math import gcd
        denom = 100
        num = round(numerator * denom)
        common = gcd(num, denom)
        return f'{num // common}/{denom // common}'

    def american_display(self) -> str:
        """Convert decimal odds to American (moneyline) format."""
        decimal = float(self.decimal_odds)
        if decimal >= 2.0:
            return f'+{round((decimal - 1) * 100)}'
        else:
            return f'{round(-100 / (decimal - 1))}'


class OddsHistory(models.Model):
    """Tracks price movements for analytics and compliance."""

    odd = models.ForeignKey(Odd, on_delete=models.CASCADE, related_name='history')
    decimal_odds = models.DecimalField(max_digits=10, decimal_places=3)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = _('Odds History')
        verbose_name_plural = _('Odds History')
        indexes = [
            models.Index(fields=['odd', 'recorded_at']),
        ]

    def __str__(self) -> str:
        return f'{self.odd.name} @ {self.decimal_odds} ({self.recorded_at:%Y-%m-%d %H:%M})'
