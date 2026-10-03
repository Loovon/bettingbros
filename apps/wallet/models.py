"""
Wallet models — user balance, transactions, and bonus ledger.
All monetary values use Decimal for precision.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Wallet(models.Model):
    """A user's financial balance. One wallet per user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
    )
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    bonus_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')

    def __str__(self) -> str:
        return f'{self.user.username} — {self.currency} {self.balance:.2f}'

    @property
    def total_balance(self) -> Decimal:
        return self.balance + self.bonus_balance


class Transaction(models.Model):
    """
    An immutable record of a financial movement.
    Never modify a transaction — create new ones for corrections.
    """

    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', _('Deposit')
        WITHDRAWAL = 'withdrawal', _('Withdrawal')
        BET_STAKE = 'bet_stake', _('Bet Stake')
        BET_WIN = 'bet_win', _('Bet Win')
        BET_REFUND = 'bet_refund', _('Bet Refund')
        BONUS_CREDIT = 'bonus_credit', _('Bonus Credit')
        BONUS_DEBIT = 'bonus_debit', _('Bonus Debit')
        ADJUSTMENT = 'adjustment', _('Adjustment')

    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        REVERSED = 'reversed', _('Reversed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_before = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
    )
    reference = models.CharField(max_length=200, blank=True, db_index=True)
    description = models.TextField(blank=True)
    payment_provider = models.CharField(max_length=100, blank=True)
    provider_transaction_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        indexes = [
            models.Index(fields=['wallet', 'transaction_type']),
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.wallet.user.username} | {self.transaction_type} | {self.amount} | {self.status}'
