"""Sportsbook serializers."""

from rest_framework import serializers

from apps.sportsbook.models import Event, League, Market, Sport, Team


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'slug', 'icon', 'is_active']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name']


class LeagueSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source='sport.name', read_only=True)

    class Meta:
        model = League
        fields = ['id', 'name', 'slug', 'sport_name']


class EventSerializer(serializers.ModelSerializer):
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)
    league = LeagueSerializer(read_only=True)
    sport_slug = serializers.CharField(source='league.sport.slug', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'slug', 'starts_at', 'status',
            'home_team', 'away_team', 'league', 'sport_slug',
            'home_score', 'away_score', 'match_time',
            'is_featured', 'betting_active',
        ]
