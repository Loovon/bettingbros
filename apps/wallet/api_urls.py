from django.urls import path
from . import api_views

app_name = "api_wallet"

urlpatterns = [
    path("balance/",           api_views.BalanceView.as_view(),           name="balance"),
    path("providers/",         api_views.AvailableProvidersView.as_view(),name="providers"),
    path("deposit/initiate/",  api_views.InitiateDepositView.as_view(),   name="deposit_initiate"),
    path("deposit/verify/",    api_views.VerifyDepositView.as_view(),     name="deposit_verify"),
]
