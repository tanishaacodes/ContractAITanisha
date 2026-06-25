"""
Force Majeure Radar & Live Data Views
=======================================
Endpoints:
  GET  /api/force-majeure/radar/live-events/          — all live FM events
  GET  /api/force-majeure/radar/risk-map/             — geospatial risk map data
  POST /api/force-majeure/radar/contract-exposure/    — live FM exposure for a contract
  GET  /api/force-majeure/radar/event-stream/         — Bloomberg-style event ticker
  GET  /api/force-majeure/radar/war-intelligence/     — live war & geopolitical data
  GET  /api/force-majeure/radar/portfolio-alerts/     — portfolio-wide live alerts
"""
import logging
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .live_data_engine import (
    fetch_all_live_events,
    fetch_gdelt_events,
    fetch_earthquake_events,
    fetch_reliefweb_disasters,
    fetch_newsapi_events,
    fetch_sanctions_alerts,
    build_risk_map_data,
    analyze_contract_fm_exposure,
    FM_CLASSIFIER,
    RISK_REGIONS,
)

logger = logging.getLogger(__name__)


class FMRadarLiveEventsView(APIView):
    """
    GET /api/force-majeure/radar/live-events/
    Returns all live FM-relevant events from GDELT + USGS + ReliefWeb + NewsAPI.
    Query params:
      ?source=gdelt|usgs|reliefweb|newsapi|all  (default: all)
      ?event_type=war|sanctions|pandemic|...
      ?min_risk=0.5
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        source = request.query_params.get('source', 'all')
        event_type_filter = request.query_params.get('event_type', '')
        min_risk = float(request.query_params.get('min_risk', 0))

        try:
            if source == 'gdelt':
                events = fetch_gdelt_events(20)
                summary = {'gdelt': len(events)}
            elif source == 'usgs':
                events = fetch_earthquake_events()
                summary = {'usgs': len(events)}
            elif source == 'reliefweb':
                events = fetch_reliefweb_disasters()
                summary = {'reliefweb': len(events)}
            elif source == 'newsapi':
                events = fetch_newsapi_events(20)
                summary = {'newsapi': len(events)}
            else:
                data = fetch_all_live_events(15)
                events = data.get('events', [])
                summary = data.get('data_sources', {})

            # Apply filters
            if event_type_filter:
                events = [e for e in events if e.get('event_type') == event_type_filter]
            if min_risk > 0:
                events = [e for e in events if e.get('risk_score', 0) >= min_risk]

            # Group by event type
            by_type = {}
            for ev in events:
                t = ev.get('event_type', 'unknown')
                by_type.setdefault(t, []).append(ev)

            return Response({
                'events': events,
                'total': len(events),
                'high_risk_count': sum(1 for e in events if e.get('risk_score', 0) > 0.6),
                'by_event_type': {k: len(v) for k, v in by_type.items()},
                'data_sources': summary,
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"FM radar live events error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FMRiskMapView(APIView):
    """
    GET /api/force-majeure/radar/risk-map/
    Returns geospatial risk data for world map visualization.
    Each entry: {country, lat, lon, risk_score, event_types, event_count}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            map_data = build_risk_map_data()

            # Add color coding for frontend
            for region in map_data:
                score = region.get('risk_score', 0)
                region['color'] = (
                    '#F16667' if score > 0.7
                    else '#F79767' if score > 0.4
                    else '#68BC00'
                )
                region['severity'] = (
                    'critical' if score > 0.8
                    else 'high' if score > 0.6
                    else 'medium' if score > 0.4
                    else 'low'
                )

            # Add shipping route disruption data
            shipping_routes = [
                {'name': 'Black Sea', 'lat': 43.0, 'lon': 34.0, 'disruption_risk': 0.82, 'color': '#F16667'},
                {'name': 'Red Sea / Suez Canal', 'lat': 20.0, 'lon': 38.0, 'disruption_risk': 0.78, 'color': '#F16667'},
                {'name': 'Strait of Hormuz', 'lat': 26.5, 'lon': 56.5, 'disruption_risk': 0.70, 'color': '#F79767'},
                {'name': 'South China Sea', 'lat': 15.0, 'lon': 114.0, 'disruption_risk': 0.55, 'color': '#F79767'},
                {'name': 'Taiwan Strait', 'lat': 24.0, 'lon': 119.5, 'disruption_risk': 0.62, 'color': '#F79767'},
                {'name': 'Gulf of Aden', 'lat': 12.0, 'lon': 47.0, 'disruption_risk': 0.75, 'color': '#F16667'},
            ]

            return Response({
                'risk_regions': map_data,
                'total_regions': len(map_data),
                'high_risk_regions': sum(1 for r in map_data if r.get('risk_score', 0) > 0.6),
                'shipping_routes': shipping_routes,
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"FM risk map error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FMContractExposureView(APIView):
    """
    POST /api/force-majeure/radar/contract-exposure/
    Calculates live FM trigger probability for a specific contract
    based on current global events.
    Body: { contract_text, contract_id, contract_value }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        contract_text = data.get('contract_text', '')
        contract_id = data.get('contract_id', '')
        contract_value = float(data.get('contract_value', 0))

        if not contract_text:
            return Response({'error': 'contract_text required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = analyze_contract_fm_exposure(
                contract_text=contract_text,
                contract_id=contract_id,
                contract_value=contract_value,
            )
            return Response(result)
        except Exception as e:
            logger.error(f"FM contract exposure error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FMEventStreamView(APIView):
    """
    GET /api/force-majeure/radar/event-stream/
    Bloomberg terminal-style live event ticker.
    Returns last 20 events sorted by time with severity badges.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            data = fetch_all_live_events(8)
            events = data.get('events', [])[:20]

            # Format as Bloomberg ticker entries
            ticker = []
            for ev in events:
                score = ev.get('risk_score', 0)
                ticker.append({
                    'time': ev.get('published_at', datetime.utcnow().isoformat())[:16],
                    'title': ev.get('title', '')[:100],
                    'event_type': ev.get('event_type', 'unknown'),
                    'location': ev.get('location', 'Global'),
                    'risk_score': score,
                    'severity': 'CRITICAL' if score > 0.8 else 'HIGH' if score > 0.6 else 'MEDIUM' if score > 0.4 else 'LOW',
                    'color': '#F16667' if score > 0.6 else '#F79767' if score > 0.4 else '#68BC00',
                    'source': ev.get('source', 'Unknown'),
                    'url': ev.get('url', ''),
                })

            return Response({
                'ticker': ticker,
                'total': len(ticker),
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FMWarIntelligenceView(APIView):
    """
    GET /api/force-majeure/radar/war-intelligence/
    Live war & geopolitical intelligence combining:
    - GDELT conflict events
    - Sanctions alerts
    - High-risk region baseline scores
    - Shipping route disruptions
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            # Fetch war-specific events from GDELT
            all_events = fetch_gdelt_events(20)
            war_events = [e for e in all_events if e.get('event_type') in ['war', 'sanctions', 'terrorism', 'political_coup']]

            # Fetch sanctions
            sanctions = fetch_sanctions_alerts()

            # Build war risk by region
            war_regions = {
                k: {'country': v['country'], 'lat': v['lat'], 'lon': v['lon'],
                    'war_risk': v['base_risk'], 'events': []}
                for k, v in RISK_REGIONS.items()
            }

            # Boost from live events
            for ev in war_events:
                loc = ev.get('location', '').lower()
                for region_key, region in war_regions.items():
                    if region_key in loc or region['country'].lower() in loc:
                        region['war_risk'] = min(1.0, region['war_risk'] + 0.05)
                        region['events'].append(ev.get('title', '')[:60])

            # Top war zones
            top_war_zones = sorted(
                [{'country': v['country'], 'lat': v['lat'], 'lon': v['lon'],
                  'war_risk': round(v['war_risk'], 2), 'recent_events': v['events'][:2]}
                 for v in war_regions.values()],
                key=lambda x: -x['war_risk']
            )[:10]

            # Active shipping disruptions
            shipping_disruptions = [
                {'route': 'Red Sea / Suez Canal', 'risk': 0.82, 'cause': 'Houthi missile attacks on commercial shipping'},
                {'route': 'Black Sea', 'risk': 0.78, 'cause': 'Russia-Ukraine conflict, naval mines'},
                {'route': 'Strait of Hormuz', 'risk': 0.68, 'cause': 'Iran-US tensions, naval exercises'},
                {'route': 'Taiwan Strait', 'risk': 0.60, 'cause': 'China-Taiwan military tensions'},
                {'route': 'Gulf of Aden', 'risk': 0.74, 'cause': 'Piracy + Houthi threat'},
            ]

            return Response({
                'war_events_detected': len(war_events),
                'sanctions_count': len(sanctions),
                'top_war_zones': top_war_zones,
                'active_shipping_disruptions': shipping_disruptions,
                'recent_war_events': war_events[:10],
                'recent_sanctions': sanctions[:5],
                'global_war_risk_index': round(
                    sum(v['base_risk'] for v in list(RISK_REGIONS.values())[:10]) / 10, 2
                ),
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"FM war intelligence error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FMPortfolioAlertsView(APIView):
    """
    GET /api/force-majeure/radar/portfolio-alerts/
    Scans all contracts in the DB against live events and returns
    portfolio-wide FM exposure alerts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            # Fetch live events once
            live_data = fetch_all_live_events(10)
            live_events = live_data.get('events', [])

            # Get contracts from DB
            alerts = []
            try:
                from api.models import Contract
                contracts = Contract.objects.all().values('id', 'title', 'content')[:30]
                for contract in contracts:
                    text = contract.get('content', '') or ''
                    if not text:
                        continue
                    exposure = analyze_contract_fm_exposure(
                        contract_text=text[:2000],
                        contract_id=str(contract.get('id', '')),
                        contract_value=0,
                        live_events=live_events,
                    )
                    if exposure.get('fm_trigger_probability', 0) > 0.2:
                        alerts.append({
                            'contract_id': str(contract.get('id', '')),
                            'contract_title': contract.get('title', ''),
                            'fm_trigger_probability': exposure['fm_trigger_probability'],
                            'triggered_by': [e.get('event_type') for e in exposure.get('triggered_by_events', [])],
                            'suggested_actions': exposure.get('suggested_actions', []),
                        })
            except Exception as db_err:
                logger.warning(f"Portfolio alerts DB fetch failed: {db_err}")

            alerts.sort(key=lambda x: -x.get('fm_trigger_probability', 0))

            return Response({
                'portfolio_alerts': alerts[:20],
                'total_alerts': len(alerts),
                'critical_alerts': sum(1 for a in alerts if a.get('fm_trigger_probability', 0) > 0.6),
                'live_events_analyzed': len(live_events),
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"FM portfolio alerts error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# BALTIC DRY INDEX VIEW
# ═══════════════════════════════════════════════════════════════════════════════
class FMBalticDryView(APIView):
    """
    GET /api/force-majeure/radar/baltic-dry/
    Returns Baltic Dry Index with FM signal strength.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        from .live_data_engine import fetch_baltic_dry_index
        try:
            data = fetch_baltic_dry_index()
            return Response(data)
        except Exception as e:
            logger.error(f'Baltic Dry error: {e}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# REAL-TIME ALERT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class FMAlertEngineView(APIView):
    """
    GET /api/force-majeure/alert-engine/
    Matches live events against all contracts and returns per-contract alerts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        from .live_data_engine import fetch_all_live_events
        from .bayesian_engine import update_priors_from_live_events, get_fm_bayesian_engine
        from .models import FMPrediction

        try:
            live_events = fetch_all_live_events().get('events', [])
            prior_updates = update_priors_from_live_events(live_events)
            engine = get_fm_bayesian_engine()

            # Build boosted evidence from updated priors
            boosted_evidence = {
                node: data['updated_prior']
                for node, data in prior_updates.items()
                if data['delta'] > 0.02
            }

            # Assess FM risk with boosted evidence
            boosted_risk = engine.compute_fm_risk_score(boosted_evidence) if boosted_evidence else 0.0

            # Get recent predictions to cross-match
            predictions = list(FMPrediction.objects.order_by('-created_at')[:50].values(
                'id', 'contract_id', 'fm_risk_score', 'created_at'
            ))

            alerts = []
            for pred in predictions:
                base_risk = float(pred.get('fm_risk_score', 0))
                delta = boosted_risk - base_risk

                # Only alert if there's a meaningful change OR high absolute risk
                if delta > 0.02 or (boosted_risk > 0.70 and base_risk < 0.65):
                    # Determine severity based on BOTH delta and absolute risk
                    # Priority 1: Large delta (rapid change is critical)
                    if delta > 0.15:
                        severity = 'CRITICAL'
                    elif delta > 0.08:
                        severity = 'HIGH'
                    # Priority 2: High absolute risk with moderate delta
                    elif boosted_risk > 0.85 and delta > 0.03:
                        severity = 'CRITICAL'
                    elif boosted_risk > 0.70 and delta > 0.02:
                        severity = 'HIGH'
                    # Priority 3: Moderate changes
                    elif delta > 0.04:
                        severity = 'MEDIUM'
                    # Default: Low priority
                    else:
                        severity = 'LOW'

                    alerts.append({
                        'contract_id': str(pred['contract_id']),
                        'prediction_id': str(pred['id']),
                        'baseline_risk': round(base_risk, 4),
                        'current_live_risk': round(boosted_risk, 4),
                        'risk_delta': round(delta, 4),
                        'severity': severity,
                        'triggered_by': [ev.get('event_type', 'unknown') for ev in live_events[:3]],
                        'alert_message': f'Live events raised FM risk by {round(delta*100, 1)}% — review contract immediately.',
                        'created_at': pred['created_at'].isoformat() if hasattr(pred['created_at'], 'isoformat') else str(pred['created_at']),
                    })

            alerts.sort(key=lambda a: -a['risk_delta'])

            # Aggregate event type counts
            event_type_counts = {}
            for ev in live_events:
                et = ev.get('event_type', 'unknown')
                event_type_counts[et] = event_type_counts.get(et, 0) + 1

            return Response({
                'alerts': alerts[:20],
                'total_alerts': len(alerts),
                'critical_count': sum(1 for a in alerts if a['severity'] == 'CRITICAL'),
                'high_count': sum(1 for a in alerts if a['severity'] == 'HIGH'),
                'live_events_processed': len(live_events),
                'event_type_breakdown': event_type_counts,
                'boosted_risk_score': round(boosted_risk, 4),
                'boosted_nodes': list(boosted_evidence.keys()),
                'last_updated': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f'FM Alert Engine error: {e}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
