"""
apps/payments/service.py
Payment provider abstraction — swap providers without changing wallet logic.
All provider integrations are thin wrappers around settings keys.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str = ""
    redirect_url: str = ""
    error: str = ""
    raw: dict = None

    def __post_init__(self):
        if self.raw is None:
            self.raw = {}


class BaseProvider:
    name: str = "base"
    supports_deposits = True
    supports_withdrawals = False

    def initiate_deposit(self, *, user, amount: Decimal, currency: str, callback_url: str, **kw) -> PaymentResult:
        raise NotImplementedError

    def verify_transaction(self, transaction_id: str) -> PaymentResult:
        raise NotImplementedError


class FlutterwaveProvider(BaseProvider):
    """Pan-African: MTN, Airtel, Zamtel, Visa, Mastercard, Mobile Money."""
    name = "flutterwave"
    supports_withdrawals = True

    def initiate_deposit(self, *, user, amount: Decimal, currency: str, callback_url: str, payment_method="card", **kw) -> PaymentResult:
        if not settings.FLUTTERWAVE_SECRET_KEY:
            return PaymentResult(False, error="Flutterwave not configured.")
        payload = {
            "tx_ref": f"bp-{user.id}-{int(amount*100)}",
            "amount": str(amount),
            "currency": currency,
            "redirect_url": callback_url,
            "payment_options": payment_method,
            "customer": {"email": user.email, "name": user.get_full_name() or user.username},
            "customizations": {"title": "BetPlatform Deposit", "logo": ""},
        }
        try:
            r = requests.post(
                "https://api.flutterwave.com/v3/payments",
                json=payload,
                headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"},
                timeout=15,
            )
            data = r.json()
            if data.get("status") == "success":
                return PaymentResult(True, redirect_url=data["data"]["link"], raw=data)
            return PaymentResult(False, error=data.get("message", "Flutterwave error"), raw=data)
        except Exception as e:
            logger.error("Flutterwave deposit error: %s", e)
            return PaymentResult(False, error="Payment provider unavailable.")

    def verify_transaction(self, transaction_id: str) -> PaymentResult:
        if not settings.FLUTTERWAVE_SECRET_KEY:
            return PaymentResult(False, error="Not configured.")
        try:
            r = requests.get(
                f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
                headers={"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"},
                timeout=15,
            )
            data = r.json()
            ok = data.get("status") == "success" and data.get("data", {}).get("status") == "successful"
            return PaymentResult(ok, transaction_id=str(transaction_id), raw=data)
        except Exception as e:
            logger.error("Flutterwave verify error: %s", e)
            return PaymentResult(False, error=str(e))


class PaystackProvider(BaseProvider):
    """Paystack — cards + mobile money, strong in West Africa."""
    name = "paystack"

    def initiate_deposit(self, *, user, amount: Decimal, currency: str, callback_url: str, **kw) -> PaymentResult:
        if not settings.PAYSTACK_SECRET_KEY:
            return PaymentResult(False, error="Paystack not configured.")
        amount_kobo = int(amount * 100)  # Paystack uses smallest currency unit
        try:
            r = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json={"email": user.email, "amount": amount_kobo, "currency": currency, "callback_url": callback_url},
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
                timeout=15,
            )
            data = r.json()
            if data.get("status"):
                return PaymentResult(True, transaction_id=data["data"]["reference"],
                                     redirect_url=data["data"]["authorization_url"], raw=data)
            return PaymentResult(False, error=data.get("message", "Paystack error"), raw=data)
        except Exception as e:
            logger.error("Paystack deposit error: %s", e)
            return PaymentResult(False, error="Payment provider unavailable.")

    def verify_transaction(self, transaction_id: str) -> PaymentResult:
        if not settings.PAYSTACK_SECRET_KEY:
            return PaymentResult(False, error="Not configured.")
        try:
            r = requests.get(
                f"https://api.paystack.co/transaction/verify/{transaction_id}",
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
                timeout=15,
            )
            data = r.json()
            ok = data.get("data", {}).get("status") == "success"
            return PaymentResult(ok, transaction_id=str(transaction_id), raw=data)
        except Exception as e:
            return PaymentResult(False, error=str(e))


class StripeProvider(BaseProvider):
    """Stripe — international cards, Apple Pay, Google Pay."""
    name = "stripe"
    supports_withdrawals = True

    def initiate_deposit(self, *, user, amount: Decimal, currency: str, callback_url: str, **kw) -> PaymentResult:
        if not settings.STRIPE_SECRET_KEY:
            return PaymentResult(False, error="Stripe not configured.")
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": "BetPlatform Deposit"},
                    "unit_amount": int(amount * 100),
                }, "quantity": 1}],
                mode="payment",
                success_url=callback_url + "?status=success&session_id={CHECKOUT_SESSION_ID}",
                cancel_url=callback_url + "?status=cancel",
                metadata={"user_id": str(user.id)},
            )
            return PaymentResult(True, transaction_id=session.id, redirect_url=session.url)
        except Exception as e:
            logger.error("Stripe error: %s", e)
            return PaymentResult(False, error="Stripe unavailable. Try another method.")


class PayPalProvider(BaseProvider):
    """PayPal — international wallets."""
    name = "paypal"

    def _get_token(self) -> Optional[str]:
        r = requests.post(
            f"https://{'api-m.sandbox' if settings.PAYPAL_MODE == 'sandbox' else 'api-m'}.paypal.com/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            timeout=10,
        )
        return r.json().get("access_token")

    def initiate_deposit(self, *, user, amount: Decimal, currency: str, callback_url: str, **kw) -> PaymentResult:
        if not settings.PAYPAL_CLIENT_ID:
            return PaymentResult(False, error="PayPal not configured.")
        try:
            token = self._get_token()
            base = f"https://{'api-m.sandbox' if settings.PAYPAL_MODE == 'sandbox' else 'api-m'}.paypal.com"
            r = requests.post(f"{base}/v2/checkout/orders", json={
                "intent": "CAPTURE",
                "purchase_units": [{"amount": {"currency_code": currency, "value": str(amount)}}],
                "application_context": {"return_url": callback_url, "cancel_url": callback_url},
            }, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, timeout=15)
            data = r.json()
            link = next((l["href"] for l in data.get("links", []) if l["rel"] == "approve"), "")
            return PaymentResult(bool(link), transaction_id=data.get("id", ""), redirect_url=link, raw=data)
        except Exception as e:
            logger.error("PayPal error: %s", e)
            return PaymentResult(False, error="PayPal unavailable.")


# Provider registry
_PROVIDERS: dict[str, BaseProvider] = {
    "flutterwave": FlutterwaveProvider(),
    "paystack":    PaystackProvider(),
    "stripe":      StripeProvider(),
    "paypal":      PayPalProvider(),
}


def get_provider(code: str) -> Optional[BaseProvider]:
    return _PROVIDERS.get(code)


def available_providers(for_deposits=True, for_withdrawals=False) -> list[dict]:
    """Returns list of configured (non-empty key) providers."""
    from apps.payments.models import PaymentProviderConfig
    active = PaymentProviderConfig.objects.filter(
        is_active=True,
        supports_deposits=for_deposits if for_deposits else True,
    ).order_by("display_order")
    result = []
    for cfg in active:
        provider = _PROVIDERS.get(cfg.provider_code)
        if provider:
            result.append({
                "code":   cfg.provider_code,
                "name":   cfg.name,
                "logo":   cfg.logo.url if cfg.logo else None,
                "min":    cfg.min_deposit,
                "max":    cfg.max_deposit,
                "regions": _PROVIDER_REGIONS.get(cfg.provider_code, []),
            })
    return result


_PROVIDER_REGIONS = {
    "stripe":      ["International", "US", "EU", "UK"],
    "paypal":      ["International", "US", "EU"],
    "flutterwave": ["Zambia", "Zimbabwe", "Nigeria", "Ghana", "Kenya", "Rwanda", "Uganda", "Tanzania"],
    "paystack":    ["Nigeria", "Ghana", "South Africa", "Kenya"],
}
