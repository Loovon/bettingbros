"""
Payments models — Payment methods and provider abstraction.
Payment providers (Stripe, PayPal, etc.) plug in via the PaymentProvider interface
without touching wallet logic.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.Model):
    """A saved payment method for a user."""

    class MethodType(models.TextChoices):
        CARD = 'card', _('Credit/Debit Card')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        E_WALLET = 'e_wallet', _('E-Wallet')
        CRYPTO = 'crypto', _('Cryptocurrency')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods',
    )
    method_type = models.CharField(max_length=20, choices=MethodType.choices)
    provider = models.CharField(max_length=100, help_text='e.g. stripe, paypal, skrill')
    display_name = models.CharField(max_length=100, help_text='e.g. Visa **** 4242')

    # Token/reference from payment provider — never store raw card numbers
    provider_token = models.CharField(max_length=500, blank=True,
                                      help_text='Provider-issued token, not raw card data')
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')

    def __str__(self) -> str:
        return f'{self.user.username} — {self.display_name}'


class PaymentProviderConfig(models.Model):
    """
    Configuration for a payment provider integration.
    Managed from the admin panel.
    API keys are environment variables; this model stores non-sensitive config.
    """

    name = models.CharField(max_length=100, unique=True)
    provider_code = models.CharField(max_length=50, unique=True,
                                     help_text='Internal code used in code, e.g. stripe')
    is_active = models.BooleanField(default=True)
    supports_deposits = models.BooleanField(default=True)
    supports_withdrawals = models.BooleanField(default=True)
    min_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    max_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    min_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=20)
    max_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    display_order = models.PositiveSmallIntegerField(default=0)
    logo = models.ImageField(upload_to='payment_providers/', null=True, blank=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = _('Payment Provider Config')
        verbose_name_plural = _('Payment Provider Configs')

    def __str__(self) -> str:
        return f'{self.name} ({"active" if self.is_active else "inactive"})'
