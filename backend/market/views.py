"""
Market Feed API Views
=====================
Provides endpoints to fetch and cache market signals for the Strategic Radar.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .market_feed import get_all_signals, get_steel_price, get_interest_rate, get_usd_inr, get_crude_oil
from .models import MarketSignal

logger = logging.getLogger(__name__)


class MarketSignalsView(APIView):
    """
    GET  /api/market/signals/
    Returns all current market signals (live fetch + DB save).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            signals = get_all_signals()

            # Persist to DB for history
            saved = []
            for sig in signals:
                if sig.get('current_value') is not None:
                    obj = MarketSignal.objects.create(
                        signal_type=sig['signal_type'],
                        signal_name=sig['signal_name'],
                        ticker=sig.get('ticker', ''),
                        current_value=sig['current_value'],
                        previous_value=sig.get('previous_value'),
                        percent_change=sig['percent_change'],
                        status=sig.get('status', 'live'),
                    )
                    saved.append(obj.id)

            return Response({
                "signals": signals,
                "saved_count": len(saved),
                "status": "ok",
            })
        except Exception as e:
            logger.error(f"Market signals fetch error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketSignalHistoryView(APIView):
    """
    GET  /api/market/history/?signal_type=commodity
    Returns last 50 stored signal records filtered by type.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        signal_type = request.query_params.get('signal_type')
        qs = MarketSignal.objects.all()[:50]
        if signal_type:
            qs = MarketSignal.objects.filter(signal_type=signal_type)[:50]

        data = list(qs.values(
            'id', 'signal_type', 'signal_name', 'ticker',
            'current_value', 'previous_value', 'percent_change',
            'status', 'fetched_at'
        ))
        return Response({"history": data, "count": len(data)})
