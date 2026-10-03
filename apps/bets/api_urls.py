from django.urls import path
from . import api_views

app_name = 'api_bets'

urlpatterns = [
    path('place/', api_views.PlaceBetView.as_view(), name='place_bet'),
    path('slip/add/', api_views.AddToSlipView.as_view(), name='add_to_slip'),
    path('slip/remove/', api_views.RemoveFromSlipView.as_view(), name='remove_from_slip'),
    path('slip/clear/', api_views.ClearSlipView.as_view(), name='clear_slip'),
    path('slip/', api_views.GetSlipView.as_view(), name='get_slip'),
    path('history/', api_views.BetHistoryView.as_view(), name='bet_history'),
]
