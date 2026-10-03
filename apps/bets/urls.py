from django.urls import path
from . import views

app_name = 'bets'

urlpatterns = [
    path('slip/', views.bet_slip_view, name='slip'),
    path('history/', views.bet_history_view, name='history'),
    path('open/', views.open_bets_view, name='open'),
]
