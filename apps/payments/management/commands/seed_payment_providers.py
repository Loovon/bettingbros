"""
Management command: seed_payment_providers
Seeds PaymentProviderConfig records so the deposit page shows real options.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed payment provider configurations"

    def handle(self, *args, **options):
        from apps.payments.models import PaymentProviderConfig
        from decimal import Decimal

        providers = [
            # International
            dict(name="Stripe", provider_code="stripe", display_order=1,
                 min_deposit=Decimal("5"), max_deposit=Decimal("50000"),
                 min_withdrawal=Decimal("20"), max_withdrawal=Decimal("10000"),
                 supports_deposits=True, supports_withdrawals=True),
            dict(name="PayPal", provider_code="paypal", display_order=2,
                 min_deposit=Decimal("10"), max_deposit=Decimal("20000"),
                 min_withdrawal=Decimal("20"), max_withdrawal=Decimal("5000"),
                 supports_deposits=True, supports_withdrawals=True),
            # Local / African
            dict(name="Flutterwave (MTN, Airtel, Zamtel, Cards)", provider_code="flutterwave",
                 display_order=3, min_deposit=Decimal("5"), max_deposit=Decimal("10000"),
                 min_withdrawal=Decimal("10"), max_withdrawal=Decimal("5000"),
                 supports_deposits=True, supports_withdrawals=True),
            dict(name="Paystack", provider_code="paystack", display_order=4,
                 min_deposit=Decimal("5"), max_deposit=Decimal("10000"),
                 min_withdrawal=Decimal("10"), max_withdrawal=Decimal("5000"),
                 supports_deposits=True, supports_withdrawals=False),
        ]

        for p in providers:
            obj, created = PaymentProviderConfig.objects.update_or_create(
                provider_code=p["provider_code"],
                defaults={k: v for k, v in p.items() if k != "provider_code"},
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"  {status}: {obj.name}")

        self.stdout.write(self.style.SUCCESS("Payment providers seeded."))
