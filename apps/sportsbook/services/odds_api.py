"""
apps/sportsbook/services/odds_api.py
Loads live sports data from The-Odds-API.
Usage: python manage.py sync_odds_api
Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
from __future__ import annotations
import logging
from decimal import Decimal
from typing import Any
import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)

BASE = settings.ODDS_API_BASE_URL


def _get(path: str, **params) -> Any:
    params["apiKey"] = settings.ODDS_API_KEY
    r = requests.get(f"{BASE}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def sync_sports() -> int:
    """Fetch all active sports and create/update Sport records."""
    from apps.sportsbook.models import Sport
    try:
        data = _get("/sports", all=True)
    except Exception as e:
        logger.error("sync_sports failed: %s", e)
        return 0
    created = 0
    for s in data:
        if s.get("active"):
            _, c = Sport.objects.update_or_create(
                slug=s["key"],
                defaults={"name": s["title"], "is_active": True},
            )
            if c: created += 1
    logger.info("sync_sports: %d sports synced", len(data))
    return created


def sync_events(sport_key: str, regions: str = "eu,uk,us") -> int:
    """Fetch upcoming events + odds for a sport, persist to DB."""
    from apps.sportsbook.models import Sport, League, Team, Event, Market, Country
    from apps.odds.models import Odd
    try:
        data = _get(f"/sports/{sport_key}/odds",
                    regions=regions, markets="h2h", dateFormat="iso", oddsFormat="decimal")
    except Exception as e:
        logger.error("sync_events failed for %s: %s", sport_key, e)
        return 0

    sport = Sport.objects.filter(slug=sport_key).first()
    if not sport:
        logger.warning("Sport %s not in DB — run sync_sports first", sport_key)
        return 0

    intl, _ = Country.objects.get_or_create(code="INT", defaults={"name": "International", "flag": ""})
    created = 0

    for game in data:
        league_name = game.get("sport_title", sport.name)
        league, _ = League.objects.get_or_create(
            sport=sport, name=league_name,
            defaults={"country": intl, "is_active": True, "external_id": sport_key},
        )
        home_team, _ = Team.objects.get_or_create(
            sport=sport, name=game["home_team"], defaults={"country": intl}
        )
        away_team, _ = Team.objects.get_or_create(
            sport=sport, name=game["away_team"], defaults={"country": intl}
        )
        try:
            starts_at = datetime.fromisoformat(game["commence_time"].replace("Z", "+00:00"))
        except Exception:
            continue

        event, ev_created = Event.objects.update_or_create(
            external_id=game["id"],
            defaults={
                "league": league, "home_team": home_team, "away_team": away_team,
                "starts_at": starts_at, "status": "scheduled", "betting_active": True,
            }
        )
        if ev_created:
            created += 1

        # Sync main h2h market
        market, _ = Market.objects.get_or_create(
            event=event, market_type="match_winner",
            defaults={"name": "Match Result", "is_main_market": True, "status": "open"}
        )
        market.status = "open"
        market.save(update_fields=["status"])

        for bookmaker in game.get("bookmakers", [])[:1]:  # use first bookmaker
            for mkt in bookmaker.get("markets", []):
                if mkt["key"] != "h2h":
                    continue
                for i, outcome in enumerate(mkt["outcomes"]):
                    Odd.objects.update_or_create(
                        market=market,
                        name=outcome["name"],
                        defaults={
                            "decimal_odds": Decimal(str(round(outcome["price"], 3))),
                            "display_order": i,
                            "status": "active",
                        }
                    )

    logger.info("sync_events %s: %d new events", sport_key, created)
    return created
