"""Sportsbook API views (DRF)."""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.sportsbook.models import Event, Sport
from apps.sportsbook.serializers import EventSerializer, SportSerializer


class SportListView(generics.ListAPIView):
    queryset = Sport.objects.filter(is_active=True).order_by('display_order')
    serializer_class = SportSerializer
    permission_classes = [AllowAny]


class EventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = (
            Event.objects.filter(status__in=['scheduled', 'live'], betting_active=True)
            .select_related('league__sport', 'home_team', 'away_team')
            .order_by('starts_at')
        )
        sport_slug = self.request.query_params.get('sport')
        if sport_slug:
            qs = qs.filter(league__sport__slug=sport_slug)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class EventDetailView(generics.RetrieveAPIView):
    queryset = (
        Event.objects.select_related('league__sport', 'home_team', 'away_team')
        .prefetch_related('markets__odds')
    )
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
