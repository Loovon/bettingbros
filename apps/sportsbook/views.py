"""Sportsbook views."""

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.content.models import Banner
from apps.promotions.models import Promotion
from apps.sportsbook.models import Event, League, Sport


def homepage(request):
    """
    Main sportsbook homepage.
    Loads featured events, live events, upcoming events, sports nav, and hero banners.
    Uses select_related/prefetch_related to avoid N+1 queries.
    """
    now = timezone.now()

    # Hero banners (carousel)
    hero_banners = (
        Banner.objects.filter(placement='hero_carousel', is_active=True)
        .order_by('-priority')[:6]
    )

    # Sports navigation
    sports = Sport.objects.filter(is_active=True).order_by('display_order')

    # Featured leagues
    featured_leagues = (
        League.objects.filter(is_featured=True, is_active=True)
        .select_related('sport', 'country')
        .order_by('display_order')[:10]
    )

    # Live events
    live_events = (
        Event.objects.filter(status='live', betting_active=True)
        .select_related('league__sport', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
        .order_by('league__sport__display_order', 'starts_at')[:12]
    )

    # Upcoming events (next 24h)
    upcoming_events = (
        Event.objects.filter(
            status='scheduled',
            starts_at__gt=now,
            starts_at__lt=now + timezone.timedelta(hours=24),
            betting_active=True,
        )
        .select_related('league__sport', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
        .order_by('starts_at')[:20]
    )

    # Featured events
    featured_events = (
        Event.objects.filter(is_featured=True, betting_active=True, status__in=['scheduled', 'live'])
        .select_related('league__sport', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
        .order_by('starts_at')[:6]
    )

    # Featured promotions
    promotions = (
        Promotion.objects.filter(is_active=True, is_featured=True, start_date__lte=now)
        .order_by('-priority')[:3]
    )

    context = {
        'hero_banners': hero_banners,
        'sports': sports,
        'featured_leagues': featured_leagues,
        'live_events': live_events,
        'upcoming_events': upcoming_events,
        'featured_events': featured_events,
        'promotions': promotions,
        'page_title': 'Sports Betting',
    }
    return render(request, 'sportsbook/homepage.html', context)


def sport_detail(request, sport_slug):
    """Events for a specific sport."""
    sport = get_object_or_404(Sport, slug=sport_slug, is_active=True)
    now = timezone.now()

    events_qs = (
        Event.objects.filter(
            league__sport=sport,
            status__in=['scheduled', 'live'],
            betting_active=True,
        )
        .select_related('league', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
        .order_by('status', 'starts_at')
    )

    paginator = Paginator(events_qs, 20)
    page = request.GET.get('page', 1)
    events = paginator.get_page(page)

    context = {
        'sport': sport,
        'events': events,
        'page_title': sport.name,
    }
    return render(request, 'sportsbook/sport_detail.html', context)


def event_detail(request, event_id, slug):
    """Full event page with all markets."""
    event = get_object_or_404(
        Event.objects.select_related(
            'league__sport', 'league__country', 'home_team', 'away_team'
        ).prefetch_related('markets__odds'),
        id=event_id,
    )
    context = {
        'event': event,
        'markets': event.markets.filter(status='open').order_by('display_order'),
        'page_title': str(event),
    }
    return render(request, 'sportsbook/event_detail.html', context)


def live_events(request):
    """Live events listing."""
    events = (
        Event.objects.filter(status='live', betting_active=True)
        .select_related('league__sport', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
        .order_by('league__sport__display_order', 'starts_at')
    )
    context = {
        'events': events,
        'page_title': 'Live Betting',
    }
    return render(request, 'sportsbook/live_events.html', context)
