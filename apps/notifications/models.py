"""
Notifications models — in-app notifications with email architecture hooks.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """An in-app notification for a user."""

    class NotificationType(models.TextChoices):
        BET_PLACED = 'bet_placed', _('Bet Placed')
        BET_WON = 'bet_won', _('Bet Won')
        BET_LOST = 'bet_lost', _('Bet Lost')
        BET_VOID = 'bet_void', _('Bet Void')
        DEPOSIT_SUCCESS = 'deposit_success', _('Deposit Successful')
        DEPOSIT_FAILED = 'deposit_failed', _('Deposit Failed')
        WITHDRAWAL_SUCCESS = 'withdrawal_success', _('Withdrawal Successful')
        WITHDRAWAL_FAILED = 'withdrawal_failed', _('Withdrawal Failed')
        PROMOTION = 'promotion', _('Promotion')
        SYSTEM = 'system', _('System')
        SECURITY = 'security', _('Security Alert')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, help_text='Optional URL for CTA')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} — {self.title}'
