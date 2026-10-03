"""Casino views."""

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from apps.casino.models import CasinoGame, GameCategory, GameProvider


def casino_home(request):
    categories = GameCategory.objects.filter(is_active=True).order_by('display_order')
    featured_games = (
        CasinoGame.objects.filter(is_featured=True, status='active')
        .select_related('provider', 'category')
        .order_by('-play_count')[:12]
    )
    new_games = (
        CasinoGame.objects.filter(is_new=True, status='active')
        .select_related('provider', 'category')
        .order_by('-created_at')[:8]
    )
    popular_games = (
        CasinoGame.objects.filter(status='active')
        .select_related('provider', 'category')
        .order_by('-play_count')[:12]
    )
    context = {
        'categories': categories,
        'featured_games': featured_games,
        'new_games': new_games,
        'popular_games': popular_games,
        'page_title': 'Casino',
    }
    return render(request, 'casino/home.html', context)


def category_view(request, category_slug):
    category = get_object_or_404(GameCategory, slug=category_slug, is_active=True)
    games_qs = (
        CasinoGame.objects.filter(category=category, status='active')
        .select_related('provider')
        .order_by('-is_featured', '-play_count')
    )
    paginator = Paginator(games_qs, 24)
    page = request.GET.get('page', 1)
    context = {
        'category': category,
        'games': paginator.get_page(page),
        'categories': GameCategory.objects.filter(is_active=True).order_by('display_order'),
        'page_title': category.name,
    }
    return render(request, 'casino/category.html', context)


def game_detail(request, game_id, slug):
    game = get_object_or_404(
        CasinoGame.objects.select_related('provider', 'category'),
        id=game_id,
    )
    context = {
        'game': game,
        'page_title': game.name,
    }
    return render(request, 'casino/game_detail.html', context)


def game_search(request):
    query = request.GET.get('q', '').strip()
    games = []
    if query:
        games = (
            CasinoGame.objects.filter(
                Q(name__icontains=query) | Q(provider__name__icontains=query),
                status='active',
            )
            .select_related('provider', 'category')
            .order_by('-play_count')[:30]
        )
    context = {
        'query': query,
        'games': games,
        'page_title': f'Search: {query}' if query else 'Search Games',
    }
    return render(request, 'casino/search.html', context)
