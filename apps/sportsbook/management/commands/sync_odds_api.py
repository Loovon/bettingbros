"""
Management command: sync_odds_api
Usage: python manage.py sync_odds_api [--sports soccer_epl soccer_efl_champ ...]
Fetches live sports data from The-Odds-API and saves to DB.
Requires ODDS_API_KEY in .env
"""
from django.core.management.base import BaseCommand
from apps.sportsbook.services.odds_api import sync_sports, sync_events


class Command(BaseCommand):
    help = "Sync sports, fixtures and odds from The-Odds-API"

    def add_arguments(self, parser):
        parser.add_argument("--sports", nargs="*",
            default=["soccer_epl", "soccer_uefa_champs_league",
                     "basketball_nba", "tennis_atp_french_open"],
            help="Sport keys to sync (space-separated)")

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.ODDS_API_KEY:
            self.stdout.write(self.style.WARNING(
                "ODDS_API_KEY not set. Add it to .env to load live data."))
            return

        self.stdout.write("Syncing sports...")
        n = sync_sports()
        self.stdout.write(self.style.SUCCESS(f"  {n} new sports"))

        for key in options["sports"]:
            self.stdout.write(f"Syncing {key}...")
            n = sync_events(key)
            self.stdout.write(self.style.SUCCESS(f"  {n} new events for {key}"))

        self.stdout.write(self.style.SUCCESS("Sync complete."))
