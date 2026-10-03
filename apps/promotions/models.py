"""
Promotions models — Promotions, Campaigns, Free Bets.
All promotions must clearly state terms and conditions.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Promotion(models.Model):
    """A promotional offer (welcome bonus, free bet, deposit match, etc.)."""

    class PromotionType(models.TextChoices):
        WELCOME_BONUS = 'welcome_bonus', _('Welcome Bonus')
        FREE_BET = 'free_bet', _('Free Bet')
        DEPOSIT_MATCH = 'deposit_match', _('Deposit Match')
        CASHBACK = 'cashback', _('Cashback')
        ENHANCED_ODDS = 'enhanced_odds', _('Enhanced Odds')
        CASINO_BONUS = 'casino_bonus', _('Casino Bonus')
        LOYALTY = 'loyalty', _('Loyalty Reward')
        OTHER = 'other', _('Other')

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    promotion_type = models.CharField(max_length=30, choices=PromotionType.choices)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    terms_and_conditions = models.TextField(
        help_text='Full T&Cs must be disclosed. Mandatory for legal compliance.'
    )
    image = models.ImageField(upload_to='promotions/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='promotions/thumbnails/', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    priority = models.PositiveSmallIntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    # Bonus value fields
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wagering_requirement = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='e.g. 30 means 30x rollover requirement',
    )
    max_bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-start_date']
        verbose_name = _('Promotion')
        verbose_name_plural = _('Promotions')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

    @property
    def is_currently_active(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class UserPromotion(models.Model):
    """Tracks which promotions a user has claimed."""

    class ClaimStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        EXPIRED = 'expired', _('Expired')
        FORFEITED = 'forfeited', _('Forfeited')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='promotions')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='claims')
    status = models.CharField(max_length=15, choices=ClaimStatus.choices, default=ClaimStatus.PENDING)
    claimed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    bonus_credited = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wagering_completed = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = [['user', 'promotion']]
        verbose_name = _('User Promotion')
        verbose_name_plural = _('User Promotions')

    def __str__(self) -> str:
        return f'{self.user.username} — {self.promotion.title} ({self.status})'
