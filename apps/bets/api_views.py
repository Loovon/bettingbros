"""
Bets API views — bet slip management and bet placement.
All odds/stake/payout values are recalculated server-side.
"""

import json
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bets.models import Bet, BetSelection
from apps.odds.models import Odd


class AddToSlipView(APIView):
    """Add an odds selection to the session-based bet slip."""
    permission_classes = []  # Allow anonymous bet slip

    def post(self, request):
        odd_id = request.data.get('odd_id')
        if not odd_id:
            return Response({'error': 'odd_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            odd = Odd.objects.select_related(
                'market__event__home_team',
                'market__event__away_team',
                'market__event__league__sport',
            ).get(id=odd_id, status='active')
        except Odd.DoesNotExist:
            return Response({'error': 'Odd not found or suspended'}, status=status.HTTP_404_NOT_FOUND)

        slip = request.session.get('bet_slip', [])

        # Prevent duplicate — remove existing selection from same market
        slip = [s for s in slip if s.get('market_id') != odd.market_id]

        slip.append({
            'odd_id': str(odd.id),
            'market_id': odd.market_id,
            'event_id': odd.market.event_id,
            'event_name': str(odd.market.event),
            'market_name': odd.market.name,
            'selection_name': odd.name,
            'odds': str(odd.decimal_odds),
        })

        request.session['bet_slip'] = slip
        request.session.modified = True

        return Response({'count': len(slip), 'slip': slip})


class RemoveFromSlipView(APIView):
    permission_classes = []

    def post(self, request):
        odd_id = str(request.data.get('odd_id', ''))
        slip = request.session.get('bet_slip', [])
        slip = [s for s in slip if s.get('odd_id') != odd_id]
        request.session['bet_slip'] = slip
        request.session.modified = True
        return Response({'count': len(slip), 'slip': slip})


class ClearSlipView(APIView):
    permission_classes = []

    def post(self, request):
        request.session['bet_slip'] = []
        request.session.modified = True
        return Response({'count': 0, 'slip': []})


class GetSlipView(APIView):
    permission_classes = []

    def get(self, request):
        slip = request.session.get('bet_slip', [])
        return Response({'count': len(slip), 'slip': slip})


class PlaceBetView(APIView):
    """
    Place a bet from the current bet slip.
    SERVER-SIDE RECALCULATION: we never trust the stake/odds from the client.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        stake_raw = request.data.get('stake')
        bet_type = request.data.get('bet_type', 'single')

        # Validate stake
        try:
            stake = Decimal(str(stake_raw)).quantize(Decimal('0.01'))
            if stake <= 0:
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            return Response({'error': 'Invalid stake amount.'}, status=status.HTTP_400_BAD_REQUEST)

        slip = request.session.get('bet_slip', [])
        if not slip:
            return Response({'error': 'Bet slip is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Re-fetch live odds from DB — never trust client-sent odds
        odd_ids = [int(s['odd_id']) for s in slip]
        odds_qs = {
            str(o.id): o
            for o in Odd.objects.filter(id__in=odd_ids, status='active').select_related('market__event')
        }

        if len(odds_qs) != len(slip):
            return Response(
                {'error': 'One or more selections are no longer available.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate total odds server-side
        total_odds = Decimal('1.000')
        for s in slip:
            total_odds *= odds_qs[s['odd_id']].decimal_odds

        total_odds = total_odds.quantize(Decimal('0.001'))
        potential_return = (stake * total_odds).quantize(Decimal('0.01'))

        # Check wallet balance
        try:
            wallet = request.user.wallet
        except Exception:
            return Response({'error': 'Wallet not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if wallet.balance < stake:
            return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        # Place bet atomically
        with db_transaction.atomic():
            from apps.wallet.models import Transaction
            balance_before = wallet.balance
            wallet.balance -= stake
            wallet.save(update_fields=['balance'])

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='bet_stake',
                amount=-stake,
                balance_before=balance_before,
                balance_after=wallet.balance,
                status='completed',
                description=f'{bet_type.capitalize()} bet placed',
            )

            bet = Bet.objects.create(
                user=request.user,
                bet_type=bet_type,
                stake=stake,
                total_odds=total_odds,
                potential_return=potential_return,
                ip_address=request.META.get('REMOTE_ADDR'),
            )

            for s in slip:
                odd = odds_qs[s['odd_id']]
                BetSelection.objects.create(
                    bet=bet,
                    odd=odd,
                    odds_at_placement=odd.decimal_odds,
                    selection_name=odd.name,
                    event_name=str(odd.market.event),
                    market_name=odd.market.name,
                )

            # Clear slip
            request.session['bet_slip'] = []
            request.session.modified = True

        return Response({
            'success': True,
            'bet_id': str(bet.id),
            'stake': str(stake),
            'total_odds': str(total_odds),
            'potential_return': str(potential_return),
        }, status=status.HTTP_201_CREATED)


class BetHistoryView(APIView):
    """
    Returns the authenticated user's most recent bets.
    GET /api/v1/bets/history/?limit=10
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            limit = 10

        if not 1 <= limit <= 50:
            return Response(
                {'error': 'limit must be between 1 and 50'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bets = (
            Bet.objects.filter(user=request.user)
            .prefetch_related('selections')
            .order_by('-placed_at')[:limit]
        )

        data = []
        for bet in bets:
            selections = [
                {
                    'selection_name': sel.selection_name,
                    'market_name': sel.market_name,
                    'event_name': sel.event_name,
                    'odds_at_placement': str(sel.odds_at_placement),
                    'result': sel.result,
                }
                for sel in bet.selections.all()
            ]
            data.append({
                'id': str(bet.id),
                'bet_type': bet.bet_type,
                'status': bet.status,
                'stake': str(bet.stake),
                'total_odds': str(bet.total_odds),
                'potential_return': str(bet.potential_return),
                'actual_return': str(bet.actual_return),
                'placed_at': bet.placed_at.isoformat(),
                'selections': selections,
            })

        return Response(data)
