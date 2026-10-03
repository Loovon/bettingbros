"""Odds serializers."""

from rest_framework import serializers

from apps.odds.models import Odd


class OddSerializer(serializers.ModelSerializer):
    market_name = serializers.CharField(source='market.name', read_only=True)

    class Meta:
        model = Odd
        fields = [
            'id', 'name', 'decimal_odds', 'handicap',
            'status', 'display_order', 'market_id', 'market_name',
        ]
