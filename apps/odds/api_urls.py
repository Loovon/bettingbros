from django.urls import path
from . import api_views

app_name = 'api_odds'

urlpatterns = [
    path('event/<int:event_id>/', api_views.EventOddsView.as_view(), name='event_odds'),
    path('market/<int:market_id>/', api_views.MarketOddsView.as_view(), name='market_odds'),
]
