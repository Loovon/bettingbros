"""
Bets models — BetSlip, Bet, BetSelection.
All validation and payout calculation is performed server-side.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Bet(models.Model):
    """
    A placed bet.  May contain one or more BetSelections.
    A single-selection bet = 'single'.
    Multiple selections = 'accumulator'.
    """

    class BetType(models.TextChoices):
        SINGLE = 'single', _('Single')
        ACCUMULATOR = 'accumulator', _('Accumulator')
        SYSTEM = 'system', _('System')

    class BetStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        WON = 'won', _('Won')
        LOST = 'lost', _('Lost')
        VOID = 'void', _('Void')
        CASHED_OUT = 'cashed_out', _('Cashed Out')
        PARTIALLY_CASHED_OUT = 'partially_cashed_out', _('Partially Cashed Out')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bets',
    )
    bet_type = models.CharField(max_length=20, choices=BetType.choices, default=BetType.SINGLE)
    status = models.CharField(
        max_length=25,
        choices=BetStatus.choices,
        default=BetStatus.OPEN,
        db_index=True,
    )

    # Stake and odds — always recorded at time of placement (server-side)
    stake = models.DecimalField(max_digits=12, decimal_places=2)
    total_odds = models.DecimalField(max_digits=10, decimal_places=3)
    potential_return = models.DecimalField(max_digits=14, decimal_places=2)
    actual_return = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    # Cash-out
    cash_out_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cashed_out_at = models.DateTimeField(null=True, blank=True)

    # Audit
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-placed_at']
        verbose_name = _('Bet')
        verbose_name_plural = _('Bets')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'placed_at']),
            models.Index(fields=['status', 'placed_at']),
        ]

    def __str__(self) -> str:
        return f'Bet #{self.id} — {self.user.username} — {self.bet_type} — {self.status}'

    def calculate_potential_return(self) -> Decimal:
        """Server-side calculation. Never trust client-provided values."""
        return (self.stake * self.total_odds).quantize(Decimal('0.01'))


class BetSelection(models.Model):
    """
    A single selection within a bet.
    References the Odd at the time of placement to preserve history.
    """

    class SelectionResult(models.TextChoices):
        PENDING = 'pending', _('Pending')
        WON = 'won', _('Won')
        LOST = 'lost', _('Lost')
        VOID = 'void', _('Void')

    bet = models.ForeignKey(Bet, on_delete=models.CASCADE, related_name='selections')

    # Snapshot of the odd at placement time
    odd = models.ForeignKey(
        'odds.Odd',
        on_delete=models.PROTECT,
        related_name='bet_selections',
    )
    odds_at_placement = models.DecimalField(max_digits=10, decimal_places=3)
    selection_name = models.CharField(max_length=200)
    event_name = models.CharField(max_length=300)
    market_name = models.CharField(max_length=200)

    result = models.CharField(
        max_length=10,
        choices=SelectionResult.choices,
        default=SelectionResult.PENDING,
    )

    class Meta:
        verbose_name = _('Bet Selection')
        verbose_name_plural = _('Bet Selections')

    def __str__(self) -> str:
        return f'{self.selection_name} @ {self.odds_at_placement} ({self.result})'
