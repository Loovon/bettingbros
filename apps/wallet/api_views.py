"""
apps/wallet/api_views.py
Wallet API: balance, deposit initiation, payment verification.
"""
from decimal import Decimal, InvalidOperation
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.wallet.models import Transaction, Wallet
from apps.payments.service import get_provider, available_providers
import logging

logger = logging.getLogger(__name__)


class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "balance": str(wallet.balance),
            "bonus_balance": str(wallet.bonus_balance),
            "total": str(wallet.total_balance),
            "currency": wallet.currency,
        })


class AvailableProvidersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(available_providers(for_deposits=True))


class InitiateDepositView(APIView):
    """Start a deposit — returns redirect_url for the payment provider."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider_code = request.data.get("provider")
        amount_raw    = request.data.get("amount")
        currency      = request.data.get("currency", request.user.currency or "USD")
        callback_url  = request.data.get("callback_url", "")

        if not provider_code:
            return Response({"error": "provider required"}, status=400)

        try:
            amount = Decimal(str(amount_raw)).quantize(Decimal("0.01"))
            if amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            return Response({"error": "Invalid amount."}, status=400)

        provider = get_provider(provider_code)
        if not provider:
            return Response({"error": f"Unknown provider: {provider_code}"}, status=400)

        result = provider.initiate_deposit(
            user=request.user, amount=amount, currency=currency,
            callback_url=callback_url or f"https://betplatform.com/wallet/callback/{provider_code}/",
        )

        if result.success:
            # Record pending transaction
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            Transaction.objects.create(
                wallet=wallet,
                transaction_type="deposit",
                amount=amount,
                balance_before=wallet.balance,
                balance_after=wallet.balance,  # will update on verification
                status="pending",
                payment_provider=provider_code,
                provider_transaction_id=result.transaction_id,
                description=f"Deposit via {provider_code}",
            )
            return Response({
                "redirect_url": result.redirect_url,
                "transaction_id": result.transaction_id,
            })
        return Response({"error": result.error}, status=400)


class VerifyDepositView(APIView):
    """Webhook / callback endpoint — verifies and credits wallet."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider_code  = request.data.get("provider")
        transaction_id = request.data.get("transaction_id")

        if not provider_code or not transaction_id:
            return Response({"error": "provider and transaction_id required"}, status=400)

        provider = get_provider(provider_code)
        if not provider:
            return Response({"error": "Unknown provider"}, status=400)

        result = provider.verify_transaction(transaction_id)
        if not result.success:
            return Response({"error": result.error or "Verification failed"}, status=400)

        # Find and complete the pending transaction
        from django.db import transaction as dbt
        try:
            tx = Transaction.objects.get(
                wallet__user=request.user,
                provider_transaction_id=str(transaction_id),
                status="pending",
                transaction_type="deposit",
            )
            with dbt.atomic():
                wallet = tx.wallet
                wallet.balance += tx.amount
                wallet.save(update_fields=["balance"])
                tx.status = "completed"
                tx.balance_after = wallet.balance
                tx.save(update_fields=["status", "balance_after"])

            logger.info("Deposit verified: user=%s amount=%s provider=%s",
                        request.user.username, tx.amount, provider_code)
            return Response({"credited": str(tx.amount), "new_balance": str(wallet.balance)})
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found or already processed."}, status=404)
