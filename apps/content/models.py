"""
Content models — Banners, Slides, Announcements.
All content is managed from the admin panel — never hard-coded in templates.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Banner(models.Model):
    """
    A promotional or advertising banner.
    Supports multiple placements across the site.
    """

    class Placement(models.TextChoices):
        HERO_CAROUSEL = 'hero_carousel', _('Hero Carousel')
        SIDEBAR = 'sidebar', _('Sidebar')
        SPORTSBOOK_TOP = 'sportsbook_top', _('Sportsbook Top')
        CASINO_TOP = 'casino_top', _('Casino Top')
        INLINE = 'inline', _('Inline Content')
        PROMOTIONS_PAGE = 'promotions_page', _('Promotions Page')

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(upload_to='banners/mobile/', null=True, blank=True,
                                     help_text='Optimized image for mobile viewports')
    target_url = models.URLField(blank=True)
    cta_text = models.CharField(max_length=50, blank=True, help_text='Call-to-action button text')
    placement = models.CharField(max_length=30, choices=Placement.choices, default=Placement.HERO_CAROUSEL)
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveSmallIntegerField(default=0, help_text='Higher = displayed first')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'title']
        verbose_name = _('Banner')
        verbose_name_plural = _('Banners')
        indexes = [
            models.Index(fields=['placement', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'{self.title} [{self.placement}]'

    @property
    def is_currently_active(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class Announcement(models.Model):
    """Site-wide announcement bar or notification."""

    message = models.TextField()
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)
    link_url = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, blank=True)
    announcement_type = models.CharField(
        max_length=20,
        choices=[('info', 'Info'), ('warning', 'Warning'), ('promo', 'Promotion')],
        default='info',
    )

    class Meta:
        ordering = ['-priority', '-start_date']
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')

    def __str__(self) -> str:
        return self.message[:80]
