from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.wallet_dashboard, name='dashboard'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('transactions/', views.transaction_history, name='transactions'),
]
