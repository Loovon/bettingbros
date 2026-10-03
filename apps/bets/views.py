"""Bets views."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.bets.models import Bet


@login_required
def bet_slip_view(request):
    context = {'page_title': 'Bet Slip'}
    return render(request, 'bets/bet_slip.html', context)


@login_required
def bet_history_view(request):
    bets = (
        Bet.objects.filter(user=request.user)
        .prefetch_related('selections')
        .order_by('-placed_at')
    )
    paginator = Paginator(bets, 15)
    page = request.GET.get('page', 1)
    context = {
        'bets': paginator.get_page(page),
        'page_title': 'Bet History',
    }
    return render(request, 'bets/bet_history.html', context)


@login_required
def open_bets_view(request):
    bets = (
        Bet.objects.filter(user=request.user, status='open')
        .prefetch_related('selections')
        .order_by('-placed_at')
    )
    context = {
        'bets': bets,
        'page_title': 'Open Bets',
    }
    return render(request, 'bets/open_bets.html', context)
