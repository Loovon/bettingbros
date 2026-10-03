"""
Accounts models — custom User, profile, and responsible gambling settings.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Extended user model with betting-platform-specific fields.
    Uses email as the primary identifier alongside username.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text='ISO 3166-1 alpha-2 country code')
    currency = models.CharField(max_length=3, default='USD', help_text='ISO 4217 currency code')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Account status
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        CLOSED = 'closed', _('Closed')
        PENDING_VERIFICATION = 'pending', _('Pending Verification')

    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    # Verification
    is_email_verified = models.BooleanField(default=False)
    is_identity_verified = models.BooleanField(default=False)
    is_age_verified = models.BooleanField(default=False)

    # Preferences
    receive_promotions = models.BooleanField(default=True)
    receive_bet_updates = models.BooleanField(default=True)
    odds_format = models.CharField(
        max_length=10,
        choices=[('decimal', 'Decimal'), ('fractional', 'Fractional'), ('american', 'American')],
        default='decimal',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['account_status']),
        ]

    def __str__(self) -> str:
        return f'{self.username} ({self.email})'

    @property
    def full_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def is_active_account(self) -> bool:
        return self.account_status == self.AccountStatus.ACTIVE


class ResponsibleGamblingSettings(models.Model):
    """
    Per-user responsible gambling controls.
    All limits are enforced server-side before any transaction is processed.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='responsible_gambling',
    )

    # Deposit limits (per period)
    daily_deposit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    weekly_deposit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_deposit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Session / time limits
    session_time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Self-exclusion
    self_excluded = models.BooleanField(default=False)
    self_exclusion_end_date = models.DateTimeField(null=True, blank=True)

    # Reality check
    reality_check_interval_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Cool-off period
    cool_off_until = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Responsible Gambling Settings')

    def __str__(self) -> str:
        return f'RG settings for {self.user.username}'
