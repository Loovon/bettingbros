"""Odds API views."""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.odds.models import Odd
from apps.odds.serializers import OddSerializer
from apps.sportsbook.models import Market


class EventOddsView(generics.ListAPIView):
    serializer_class = OddSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Odd.objects.filter(
                market__event_id=self.kwargs['event_id'],
                market__status='open',
                status='active',
            )
            .select_related('market')
            .order_by('market__display_order', 'display_order')
        )


class MarketOddsView(generics.ListAPIView):
    serializer_class = OddSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Odd.objects.filter(
            market_id=self.kwargs['market_id'],
            status='active',
        ).order_by('display_order')
