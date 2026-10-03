"""
Root URL configuration for Betting Platform.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Platform sections
    path('', include('apps.sportsbook.urls', namespace='sportsbook')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('casino/', include('apps.casino.urls', namespace='casino')),
    path('bets/', include('apps.bets.urls', namespace='bets')),
    path('wallet/', include('apps.wallet.urls', namespace='wallet')),
    path('promotions/', include('apps.promotions.urls', namespace='promotions')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),

    # API endpoints
    path('api/v1/', include([
        path('bets/', include('apps.bets.api_urls', namespace='api_bets')),
        path('odds/', include('apps.odds.api_urls', namespace='api_odds')),
        path('wallet/', include('apps.wallet.api_urls', namespace='api_wallet')),
        path('sportsbook/', include('apps.sportsbook.api_urls', namespace='api_sportsbook')),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
