"""
Management command: seed_demo_data
Creates realistic sample sports, leagues, teams, events, markets, and odds
so the platform looks populated immediately after setup.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.sportsbook.models import Country, Event, League, Market, Sport, Team
from apps.odds.models import Odd
from apps.casino.models import CasinoGame, GameCategory, GameProvider
from apps.content.models import Announcement, Banner
from apps.promotions.models import Promotion


class Command(BaseCommand):
    help = "Seed the database with realistic demo data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")
        self._seed_countries()
        self._seed_sports()
        self._seed_leagues()
        self._seed_teams()
        self._seed_events()
        self._seed_casino()
        self._seed_content()
        self._seed_promotions()
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))

    def _seed_countries(self):
        data = [
            ("England", "GB", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
            ("Spain", "ES", "🇪🇸"),
            ("Germany", "DE", "🇩🇪"),
            ("Italy", "IT", "🇮🇹"),
            ("France", "FR", "🇫🇷"),
            ("USA", "US", "🇺🇸"),
            ("Brazil", "BR", "🇧🇷"),
            ("International", "INT", "🌍"),
        ]
        for name, code, flag in data:
            Country.objects.get_or_create(code=code, defaults={"name": name, "flag": flag})
        self.stdout.write("  Countries done")

    def _seed_sports(self):
        data = [
            ("Football", "⚽", 1), ("Basketball", "🏀", 2), ("Tennis", "🎾", 3),
            ("Baseball", "⚾", 4), ("Volleyball", "🏐", 5), ("Rugby", "🏉", 6),
            ("Cricket", "🏏", 7), ("Hockey", "🏒", 8), ("Esports", "🎮", 9),
        ]
        for name, icon, order in data:
            Sport.objects.get_or_create(name=name, defaults={"icon": icon, "display_order": order})
        self.stdout.write("  Sports done")

    def _seed_leagues(self):
        eng = Country.objects.get(code="GB")
        esp = Country.objects.get(code="ES")
        ger = Country.objects.get(code="DE")
        ita = Country.objects.get(code="IT")
        fran = Country.objects.get(code="FR")
        intl = Country.objects.get(code="INT")
        football = Sport.objects.get(name="Football")
        basketball = Sport.objects.get(name="Basketball")
        tennis = Sport.objects.get(name="Tennis")
        data = [
            (football, "Premier League", eng, True),
            (football, "La Liga", esp, True),
            (football, "Bundesliga", ger, True),
            (football, "Serie A", ita, False),
            (football, "Ligue 1", fran, False),
            (football, "UEFA Champions League", intl, True),
            (basketball, "NBA", Country.objects.get(code="US"), True),
            (tennis, "ATP World Tour", intl, True),
        ]
        for sport, name, country, featured in data:
            League.objects.get_or_create(
                sport=sport, name=name,
                defaults={"country": country, "is_featured": featured, "is_active": True}
            )
        self.stdout.write("  Leagues done")

    def _seed_teams(self):
        football = Sport.objects.get(name="Football")
        eng = Country.objects.get(code="GB")
        esp = Country.objects.get(code="ES")
        ger = Country.objects.get(code="DE")
        teams_data = [
            ("Manchester United", "MAN UTD", football, eng),
            ("Arsenal", "ARS", football, eng),
            ("Chelsea", "CHE", football, eng),
            ("Liverpool", "LIV", football, eng),
            ("Manchester City", "MCI", football, eng),
            ("Tottenham Hotspur", "TOT", football, eng),
            ("Real Madrid", "RMA", football, esp),
            ("Barcelona", "BAR", football, esp),
            ("Atletico Madrid", "ATM", football, esp),
            ("Bayern Munich", "BAY", football, ger),
            ("Borussia Dortmund", "BVB", football, ger),
        ]
        for name, short, sport, country in teams_data:
            Team.objects.get_or_create(
                name=name, sport=sport,
                defaults={"short_name": short, "country": country}
            )
        self.stdout.write("  Teams done")

    def _seed_events(self):
        premier_league = League.objects.get(name="Premier League")
        la_liga = League.objects.get(name="La Liga")
        ucl = League.objects.get(name="UEFA Champions League")
        teams = {t.name: t for t in Team.objects.all()}
        now = timezone.now()
        fixtures = [
            # Live
            (teams.get("Manchester United"), teams.get("Arsenal"), premier_league,
             now - timedelta(hours=1), "live", 1, 1, "67", True),
            (teams.get("Liverpool"), teams.get("Chelsea"), premier_league,
             now - timedelta(minutes=35), "live", 2, 0, "35", False),
            # Upcoming
            (teams.get("Real Madrid"), teams.get("Barcelona"), la_liga,
             now + timedelta(hours=3), "scheduled", None, None, "", True),
            (teams.get("Manchester City"), teams.get("Tottenham Hotspur"), premier_league,
             now + timedelta(hours=5), "scheduled", None, None, "", False),
            (teams.get("Bayern Munich"), teams.get("Borussia Dortmund"), League.objects.get(name="Bundesliga"),
             now + timedelta(hours=7), "scheduled", None, None, "", True),
            (teams.get("Atletico Madrid"), teams.get("Real Madrid"), ucl,
             now + timedelta(days=1, hours=2), "scheduled", None, None, "", True),
        ]
        for home, away, league, starts_at, status, hs, as_, mt, featured in fixtures:
            if not home or not away:
                continue
            event, created = Event.objects.get_or_create(
                home_team=home, away_team=away, league=league,
                defaults={
                    "starts_at": starts_at, "status": status,
                    "home_score": hs, "away_score": as_,
                    "match_time": mt, "is_featured": featured,
                    "betting_active": True,
                }
            )
            if created:
                self._create_markets(event)
        self.stdout.write("  Events done")

    def _create_markets(self, event):
        home = event.home_team.short_name or event.home_team.name
        away = event.away_team.short_name or event.away_team.name
        market_data = [
            ("Match Result", "match_winner", True, [
                (home, round(random.uniform(1.5, 3.5), 2)),
                ("Draw", round(random.uniform(2.8, 4.2), 2)),
                (away, round(random.uniform(1.5, 4.0), 2)),
            ]),
            ("Both Teams to Score", "btts", False, [
                ("Yes", round(random.uniform(1.5, 2.2), 2)),
                ("No", round(random.uniform(1.5, 2.5), 2)),
            ]),
            ("Total Goals Over/Under 2.5", "over_under", False, [
                ("Over 2.5", round(random.uniform(1.6, 2.2), 2)),
                ("Under 2.5", round(random.uniform(1.6, 2.2), 2)),
            ]),
        ]
        for i, (name, mtype, is_main, selections) in enumerate(market_data):
            market = Market.objects.create(
                event=event, name=name, market_type=mtype,
                is_main_market=is_main, display_order=i, status="open"
            )
            for j, (sel_name, odds) in enumerate(selections):
                Odd.objects.create(
                    market=market, name=sel_name,
                    decimal_odds=Decimal(str(odds)),
                    display_order=j, status="active"
                )

    def _seed_casino(self):
        providers_data = [
            ("Evolution Gaming", "evolution"),
            ("NetEnt", "netent"),
            ("Pragmatic Play", "pragmatic"),
            ("Microgaming", "microgaming"),
        ]
        providers = {}
        for name, code in providers_data:
            p, _ = GameProvider.objects.get_or_create(name=name, defaults={"is_active": True})
            providers[code] = p

        categories_data = [
            ("Slots", "🎰", 1), ("Live Casino", "🎰", 2),
            ("Table Games", "🃏", 3), ("Jackpots", "💰", 4),
        ]
        cats = {}
        for name, icon, order in categories_data:
            c, _ = GameCategory.objects.get_or_create(
                name=name, defaults={"icon": icon, "display_order": order}
            )
            cats[name] = c

        games_data = [
            ("Lightning Roulette", providers["evolution"], cats["Live Casino"], True, False, "97.30"),
            ("Starburst", providers["netent"], cats["Slots"], True, False, "96.09"),
            ("Sweet Bonanza", providers["pragmatic"], cats["Slots"], True, True, "96.51"),
            ("Gonzo's Quest", providers["netent"], cats["Slots"], False, True, "95.97"),
            ("Blackjack Classic", providers["evolution"], cats["Table Games"], True, False, "99.28"),
            ("Mega Moolah", providers["microgaming"], cats["Jackpots"], True, False, "88.12"),
            ("Book of Dead", providers["pragmatic"], cats["Slots"], False, True, "94.25"),
            ("Crazy Time", providers["evolution"], cats["Live Casino"], True, False, "96.08"),
        ]
        for name, provider, category, featured, is_new, rtp in games_data:
            CasinoGame.objects.get_or_create(
                name=name, provider=provider,
                defaults={
                    "category": category, "is_featured": featured,
                    "is_new": is_new, "rtp": Decimal(rtp),
                    "status": "active", "has_demo": True,
                }
            )
        self.stdout.write("  Casino done")

    def _seed_content(self):
        banners = [
            ("Welcome Bonus — Get up to 100% on your first deposit",
             "Claim your welcome offer today!", ""),
            ("Champions League Special",
             "Enhanced odds on every UCL match this week.", ""),
            ("New Casino Games Available",
             "Try our latest slots from top providers.", ""),
        ]
        for i, (title, subtitle, url) in enumerate(banners):
            Banner.objects.get_or_create(
                title=title,
                defaults={
                    "subtitle": subtitle, "target_url": url,
                    "placement": "hero_carousel", "is_active": True,
                    "priority": 10 - i, "cta_text": "Learn More",
                }
            )
        Announcement.objects.get_or_create(
            message="🎁 New to BetPlatform? Get a 100% welcome bonus on your first deposit. T&Cs apply. 18+",
            defaults={"is_active": True, "priority": 10, "announcement_type": "promo"}
        )
        self.stdout.write("  Content done")

    def _seed_promotions(self):
        now = timezone.now()
        promos = [
            ("Welcome Bonus — 100% up to $200", "welcome_bonus",
             "Get double your first deposit up to $200.",
             "Deposit $10 or more and receive a 100% matched bonus up to $200.",
             "Minimum deposit $10. Maximum bonus $200. Wagering requirement: 30x bonus amount. Valid for 30 days.",
             Decimal("200"), Decimal("10"), 30),
        ]
        for title, ptype, short_desc, desc, tc, amount, min_dep, wagering in promos:
            import django.utils.text
            slug = django.utils.text.slugify(title)
            Promotion.objects.get_or_create(
                title=title,
                defaults={
                    "promotion_type": ptype, "short_description": short_desc,
                    "description": desc, "terms_and_conditions": tc,
                    "is_active": True, "is_featured": True,
                    "start_date": now - timedelta(days=1),
                    "bonus_amount": amount, "min_deposit": min_dep,
                    "wagering_requirement": wagering, "priority": 10,
                    "slug": slug,
                }
            )
        self.stdout.write("  Promotions done")
