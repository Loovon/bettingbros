"""Wallet views."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.wallet.models import Transaction, Wallet


@login_required
def wallet_dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    recent_transactions = (
        Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:10]
    )
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'page_title': 'My Wallet',
    }
    return render(request, 'wallet/dashboard.html', context)


@login_required
def deposit_view(request):
    from apps.payments.models import PaymentProviderConfig
    providers = PaymentProviderConfig.objects.filter(is_active=True, supports_deposits=True).order_by('display_order')
    context = {
        'providers': providers,
        'page_title': 'Deposit Funds',
    }
    return render(request, 'wallet/deposit.html', context)


@login_required
def withdraw_view(request):
    from apps.payments.models import PaymentProviderConfig
    providers = PaymentProviderConfig.objects.filter(is_active=True, supports_withdrawals=True).order_by('display_order')
    context = {
        'providers': providers,
        'page_title': 'Withdraw Funds',
    }
    return render(request, 'wallet/withdraw.html', context)


@login_required
def transaction_history(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions_qs = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
    paginator = Paginator(transactions_qs, 20)
    page = request.GET.get('page', 1)
    context = {
        'wallet': wallet,
        'transactions': paginator.get_page(page),
        'page_title': 'Transaction History',
    }
    return render(request, 'wallet/transaction_history.html', context)
