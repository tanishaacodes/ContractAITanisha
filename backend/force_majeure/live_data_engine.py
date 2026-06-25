"""
Force Majeure Live Data Engine
================================
Fetches real-time global events from FREE public APIs:

1. NewsAPI           — https://newsapi.org (free tier: 100 req/day)
2. GDELT Project     — https://api.gdeltproject.org (completely free, no key)
3. USGS Earthquake   — https://earthquake.usgs.gov (completely free, no key)
4. ReliefWeb         — https://api.reliefweb.int (completely free, no key)
5. ACLED             — https://acleddata.com (free academic, no key for basic)
6. OpenWeather       — https://openweathermap.org (free tier)
7. OFAC SDN          — https://www.treasury.gov/ofac/downloads (public XML)

All free. No paid API required.
"""
import re
import json
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─── API Keys (from settings / env) ──────────────────────────────────────────
NEWS_API_KEY = getattr(settings, 'NEWS_API_KEY', '')

# ─── Cache TTL ────────────────────────────────────────────────────────────────
CACHE_TTL_NEWS = 900        # 15 min
CACHE_TTL_EARTHQUAKE = 300  # 5 min
CACHE_TTL_GDELT = 600       # 10 min
CACHE_TTL_RELIEFWEB = 1800  # 30 min

# ─── FM Event keyword classifier ─────────────────────────────────────────────
FM_CLASSIFIER = {
    'war': [
        'war', 'military conflict', 'armed conflict', 'invasion', 'missile strike',
        'military operation', 'airstrike', 'bombing', 'troops', 'military forces',
        'nato', 'warfare', 'battle', 'offensive', 'ceasefire', 'hostilities',
    ],
    'sanctions': [
        'sanctions', 'sanction', 'embargo', 'export ban', 'trade restriction',
        'ofac', 'blacklist', 'asset freeze', 'trade war', 'tariff', 'import ban',
    ],
    'pandemic': [
        'pandemic', 'epidemic', 'outbreak', 'public health emergency', 'who alert',
        'disease spread', 'quarantine', 'lockdown', 'virus outbreak', 'health crisis',
    ],
    'port_closure': [
        'port closure', 'port shutdown', 'harbor closed', 'shipping disruption',
        'suez canal', 'red sea', 'black sea', 'strait of hormuz', 'maritime',
        'shipping lane', 'naval blockade', 'vessel', 'cargo ship',
    ],
    'supply_chain_disruption': [
        'supply chain', 'supply disruption', 'factory shutdown', 'production halt',
        'logistics disruption', 'material shortage', 'chip shortage', 'fuel shortage',
    ],
    'energy_shortage': [
        'energy crisis', 'power outage', 'blackout', 'gas shortage', 'oil price',
        'energy shortage', 'power grid', 'fuel crisis', 'electricity shortage',
    ],
    'political_coup': [
        'coup', 'government overthrow', 'regime change', 'political crisis',
        'state of emergency', 'martial law', 'political instability', 'protests',
    ],
    'natural_disaster': [
        'earthquake', 'flood', 'hurricane', 'typhoon', 'cyclone', 'wildfire',
        'tsunami', 'volcanic eruption', 'tornado', 'storm surge', 'landslide',
    ],
    'cyber_attack': [
        'cyber attack', 'cyberattack', 'ransomware', 'data breach', 'hacking',
        'critical infrastructure attack', 'cyber warfare', 'ddos', 'malware',
    ],
    'terrorism': [
        'terrorism', 'terrorist attack', 'bombing', 'explosion', 'attack on',
        'suicide bomber', 'isis', 'al-qaeda', 'extremist',
    ],
}

# ─── High-risk regions & their coordinates ───────────────────────────────────
RISK_REGIONS = {
    'ukraine': {'lat': 49.0, 'lon': 32.0, 'country': 'Ukraine', 'base_risk': 0.85},
    'russia': {'lat': 61.0, 'lon': 105.0, 'country': 'Russia', 'base_risk': 0.75},
    'middle east': {'lat': 29.0, 'lon': 42.0, 'country': 'Middle East', 'base_risk': 0.65},
    'israel': {'lat': 31.0, 'lon': 35.0, 'country': 'Israel', 'base_risk': 0.80},
    'iran': {'lat': 32.0, 'lon': 53.0, 'country': 'Iran', 'base_risk': 0.78},
    'iraq': {'lat': 33.0, 'lon': 44.0, 'country': 'Iraq', 'base_risk': 0.70},
    'syria': {'lat': 35.0, 'lon': 38.0, 'country': 'Syria', 'base_risk': 0.82},
    'yemen': {'lat': 15.0, 'lon': 48.0, 'country': 'Yemen', 'base_risk': 0.88},
    'red sea': {'lat': 20.0, 'lon': 38.0, 'country': 'Red Sea', 'base_risk': 0.75},
    'black sea': {'lat': 43.0, 'lon': 34.0, 'country': 'Black Sea', 'base_risk': 0.70},
    'taiwan': {'lat': 23.5, 'lon': 121.0, 'country': 'Taiwan', 'base_risk': 0.65},
    'north korea': {'lat': 40.0, 'lon': 127.0, 'country': 'North Korea', 'base_risk': 0.80},
    'sudan': {'lat': 15.0, 'lon': 32.0, 'country': 'Sudan', 'base_risk': 0.78},
    'myanmar': {'lat': 19.0, 'lon': 96.0, 'country': 'Myanmar', 'base_risk': 0.72},
    'pakistan': {'lat': 30.0, 'lon': 69.0, 'country': 'Pakistan', 'base_risk': 0.55},
    'afghanistan': {'lat': 33.0, 'lon': 65.0, 'country': 'Afghanistan', 'base_risk': 0.82},
    'venezuela': {'lat': 8.0, 'lon': -66.0, 'country': 'Venezuela', 'base_risk': 0.60},
    'libya': {'lat': 26.0, 'lon': 17.0, 'country': 'Libya', 'base_risk': 0.75},
    'somalia': {'lat': 5.0, 'lon': 46.0, 'country': 'Somalia', 'base_risk': 0.80},
    'strait of hormuz': {'lat': 26.5, 'lon': 56.5, 'country': 'Strait of Hormuz', 'base_risk': 0.72},
}


# ─── 1. GDELT — completely free, no API key ───────────────────────────────────

def fetch_gdelt_events(max_results: int = 20) -> List[Dict]:
    """
    Fetch recent FM-relevant events from GDELT Project (free, no key).
    GDELT 2.0 DOC API — searches news articles worldwide.
    """
    cache_key = 'fm_gdelt_events'
    cached = cache.get(cache_key)
    if cached:
        return cached

    query = 'war OR sanctions OR earthquake OR flood OR pandemic OR "port closure" OR "supply chain" OR hurricane OR "cyber attack"'
    url = 'https://api.gdeltproject.org/api/v2/doc/doc'
    params = {
        'query': query,
        'mode': 'artlist',
        'maxrecords': max_results,
        'format': 'json',
        'timespan': '24h',
        'sort': 'DateDesc',
    }

    events = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get('articles', [])
            for article in articles[:max_results]:
                title = article.get('title', '')
                event_type, score = classify_fm_event(title)
                if event_type:
                    region = detect_region(title)
                    events.append({
                        'source': 'GDELT',
                        'title': title,
                        'url': article.get('url', ''),
                        'published_at': article.get('seendate', ''),
                        'event_type': event_type,
                        'risk_score': score,
                        'location': region.get('country', 'Global') if region else 'Global',
                        'lat': region.get('lat', 0) if region else 0,
                        'lon': region.get('lon', 0) if region else 0,
                    })
    except Exception as e:
        logger.warning(f"GDELT fetch failed: {e}")

    cache.set(cache_key, events, CACHE_TTL_GDELT)
    return events


# ─── 2. USGS Earthquake Feed — completely free ────────────────────────────────

def fetch_earthquake_events(min_magnitude: float = 5.0) -> List[Dict]:
    """
    Fetch recent significant earthquakes from USGS (free, no key needed).
    Returns earthquakes M5.0+ in last 7 days.
    """
    cache_key = 'fm_usgs_earthquakes'
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson'
    events = []
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for feature in data.get('features', [])[:10]:
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [0, 0, 0])
                mag = props.get('mag', 0)
                place = props.get('place', 'Unknown')
                if mag >= min_magnitude:
                    risk_score = min(1.0, (mag - 5.0) / 4.0 + 0.3)
                    events.append({
                        'source': 'USGS',
                        'title': f"M{mag} Earthquake — {place}",
                        'event_type': 'natural_disaster',
                        'risk_score': round(risk_score, 2),
                        'location': place,
                        'lat': coords[1] if len(coords) > 1 else 0,
                        'lon': coords[0] if len(coords) > 0 else 0,
                        'magnitude': mag,
                        'published_at': datetime.utcfromtimestamp(
                            props.get('time', 0) / 1000
                        ).isoformat() if props.get('time') else '',
                        'url': props.get('url', ''),
                    })
    except Exception as e:
        logger.warning(f"USGS fetch failed: {e}")

    cache.set(cache_key, events, CACHE_TTL_EARTHQUAKE)
    return events


# ─── 3. ReliefWeb — free humanitarian crisis data ─────────────────────────────

def fetch_reliefweb_disasters() -> List[Dict]:
    """
    Fetch active disasters and crises from ReliefWeb API (free, no key).
    Covers floods, conflicts, epidemics, droughts globally.
    """
    cache_key = 'fm_reliefweb_disasters'
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = 'https://api.reliefweb.int/v1/disasters'
    params = {
        'appname': 'primecontractai',
        'limit': 20,
        'filter[field]': 'status',
        'filter[value]': 'current',
        'fields[include][]': ['name', 'country', 'type', 'date', 'status', 'url'],
        'sort[]': 'date.created:desc',
    }

    events = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('data', [])[:15]:
                fields = item.get('fields', {})
                name = fields.get('name', '')
                dtype = fields.get('type', [{}])
                dtype_name = dtype[0].get('name', 'disaster') if dtype else 'disaster'
                countries = fields.get('country', [{}])
                country_name = countries[0].get('name', 'Global') if countries else 'Global'

                event_type = _map_reliefweb_type(dtype_name)
                region = detect_region(country_name + ' ' + name)
                risk_score = 0.6 if 'conflict' in dtype_name.lower() else 0.45

                events.append({
                    'source': 'ReliefWeb',
                    'title': name,
                    'event_type': event_type,
                    'risk_score': risk_score,
                    'location': country_name,
                    'lat': region.get('lat', 0) if region else 0,
                    'lon': region.get('lon', 0) if region else 0,
                    'published_at': fields.get('date', {}).get('created', ''),
                    'url': fields.get('url', ''),
                })
    except Exception as e:
        logger.warning(f"ReliefWeb fetch failed: {e}")

    cache.set(cache_key, events, CACHE_TTL_RELIEFWEB)
    return events


def _map_reliefweb_type(dtype: str) -> str:
    dtype_lower = dtype.lower()
    if any(w in dtype_lower for w in ['flood', 'cyclone', 'earthquake', 'hurricane', 'volcano', 'wildfire', 'drought']):
        return 'natural_disaster'
    if 'conflict' in dtype_lower or 'violence' in dtype_lower:
        return 'war'
    if 'epidemic' in dtype_lower or 'disease' in dtype_lower:
        return 'pandemic'
    return 'supply_chain_disruption'


# ─── 4. NewsAPI — free tier (100 req/day) ─────────────────────────────────────

def fetch_newsapi_events(max_results: int = 20) -> List[Dict]:
    """
    Fetch FM-relevant news from NewsAPI.org (free tier: 100 req/day).
    Requires NEWS_API_KEY in settings.
    """
    if not NEWS_API_KEY:
        logger.info("NEWS_API_KEY not set — skipping NewsAPI")
        return []

    cache_key = 'fm_newsapi_events'
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'q': 'war OR sanctions OR earthquake OR flood OR pandemic OR "port closure" OR hurricane OR "supply chain"',
        'language': 'en',
        'pageSize': max_results,
        'apiKey': NEWS_API_KEY,
    }

    events = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for article in data.get('articles', [])[:max_results]:
                title = article.get('title', '') or ''
                description = article.get('description', '') or ''
                text = title + ' ' + description
                event_type, score = classify_fm_event(text)
                if event_type:
                    region = detect_region(text)
                    events.append({
                        'source': 'NewsAPI',
                        'title': title,
                        'description': description,
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'event_type': event_type,
                        'risk_score': score,
                        'location': region.get('country', 'Global') if region else 'Global',
                        'lat': region.get('lat', 0) if region else 0,
                        'lon': region.get('lon', 0) if region else 0,
                    })
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed: {e}")

    cache.set(cache_key, events, CACHE_TTL_NEWS)
    return events


# ─── 5. Open-Sanctions (free OFAC/UN/EU sanctions data) ──────────────────────

def fetch_sanctions_alerts() -> List[Dict]:
    """
    Fetch recent sanctions from Open Sanctions (free, no key).
    https://api.opensanctions.org
    """
    cache_key = 'fm_sanctions_alerts'
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Use OpenSanctions datasets API
    url = 'https://api.opensanctions.org/search/default'
    params = {
        'q': 'country sanctions 2025 2026',
        'schema': 'Sanction',
        'limit': 10,
    }
    events = []
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for result in data.get('results', [])[:10]:
                caption = result.get('caption', '')
                events.append({
                    'source': 'OpenSanctions',
                    'title': f"Sanction: {caption}",
                    'event_type': 'sanctions',
                    'risk_score': 0.75,
                    'location': 'Global',
                    'lat': 0, 'lon': 0,
                    'published_at': datetime.utcnow().isoformat(),
                    'url': f"https://opensanctions.org/entities/{result.get('id', '')}",
                })
    except Exception as e:
        logger.warning(f"OpenSanctions fetch failed: {e}")

    cache.set(cache_key, events, 3600)
    return events


# ─── 6. Aggregator — combines all sources ────────────────────────────────────

def fetch_all_live_events(max_per_source: int = 15) -> Dict:
    """
    Master aggregator — fetches from all free data sources and returns
    unified event list with FM risk classifications.
    """
    all_events = []

    # GDELT (best for geopolitical — completely free)
    gdelt = fetch_gdelt_events(max_per_source)
    all_events.extend(gdelt)

    # USGS Earthquakes (completely free)
    quakes = fetch_earthquake_events()
    all_events.extend(quakes)

    # ReliefWeb (humanitarian crises — completely free)
    relief = fetch_reliefweb_disasters()
    all_events.extend(relief)

    # NewsAPI (if key available)
    news = fetch_newsapi_events(max_per_source)
    all_events.extend(news)

    # Deduplicate by title similarity
    seen_titles = set()
    deduped = []
    for ev in all_events:
        title_key = ev.get('title', '')[:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped.append(ev)

    # Sort by risk score descending
    deduped.sort(key=lambda x: x.get('risk_score', 0), reverse=True)

    # Build summary stats
    by_type = {}
    for ev in deduped:
        t = ev.get('event_type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1

    high_risk = [e for e in deduped if e.get('risk_score', 0) > 0.6]

    return {
        'events': deduped[:50],
        'total_events': len(deduped),
        'high_risk_events': len(high_risk),
        'events_by_type': by_type,
        'top_threats': deduped[:5],
        'data_sources': {
            'gdelt': len(gdelt),
            'usgs': len(quakes),
            'reliefweb': len(relief),
            'newsapi': len(news),
        },
        'last_updated': datetime.utcnow().isoformat(),
    }


# ─── 7. Live Risk Map data ────────────────────────────────────────────────────

def build_risk_map_data() -> List[Dict]:
    """
    Build geospatial risk data for the FM Risk Map.
    Returns list of {country, lat, lon, risk_score, event_type, event_count}.
    Combines base risk scores + live event detections.
    """
    cache_key = 'fm_risk_map_data'
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Start with base risk for known high-risk regions
    region_risks = {}
    for region_key, region_data in RISK_REGIONS.items():
        region_risks[region_data['country']] = {
            'country': region_data['country'],
            'lat': region_data['lat'],
            'lon': region_data['lon'],
            'risk_score': region_data['base_risk'],
            'event_types': [],
            'event_count': 0,
            'source': 'baseline',
        }

    # Boost scores from live events
    live_data = fetch_all_live_events(10)
    for event in live_data.get('events', []):
        location = event.get('location', '')
        lat = event.get('lat', 0)
        lon = event.get('lon', 0)
        score = event.get('risk_score', 0.3)
        etype = event.get('event_type', 'unknown')

        if location and location != 'Global':
            if location not in region_risks:
                region_risks[location] = {
                    'country': location,
                    'lat': lat,
                    'lon': lon,
                    'risk_score': score,
                    'event_types': [etype],
                    'event_count': 1,
                    'source': 'live',
                }
            else:
                existing = region_risks[location]
                existing['risk_score'] = min(1.0, max(existing['risk_score'], score))
                if etype not in existing['event_types']:
                    existing['event_types'].append(etype)
                existing['event_count'] += 1
                existing['source'] = 'live'

    result = list(region_risks.values())
    result.sort(key=lambda x: x['risk_score'], reverse=True)

    cache.set(cache_key, result, 600)
    return result


# ─── 8. Contract impact analyzer ─────────────────────────────────────────────

def analyze_contract_fm_exposure(
    contract_text: str,
    contract_id: str = '',
    contract_value: float = 0,
    live_events: Optional[List[Dict]] = None,
) -> Dict:
    """
    Given live events + contract text, calculate FM trigger probability.
    Formula: FM_Risk = EventProbability × ContractExposure × Dependency
    """
    if live_events is None:
        live_data = fetch_all_live_events(10)
        live_events = live_data.get('events', [])

    text_lower = contract_text.lower()
    triggered_events = []
    total_fm_risk = 0.0

    for event in live_events:
        event_type = event.get('event_type', '')
        location = event.get('location', '').lower()
        risk_score = event.get('risk_score', 0.0)

        # Check if contract text mentions the event location or type
        location_match = location and location != 'global' and location in text_lower
        type_match = any(kw in text_lower for kw in FM_CLASSIFIER.get(event_type, []))

        if location_match or type_match:
            exposure = 0.8 if location_match and type_match else 0.5
            dependency = 0.7 if location_match else 0.4
            fm_contribution = risk_score * exposure * dependency
            total_fm_risk += fm_contribution

            triggered_events.append({
                'event': event.get('title', ''),
                'event_type': event_type,
                'location': event.get('location', ''),
                'risk_score': risk_score,
                'fm_contribution': round(fm_contribution, 4),
                'location_match': location_match,
                'type_match': type_match,
            })

    fm_risk = min(1.0, total_fm_risk)
    financial_exposure = fm_risk * contract_value if contract_value > 0 else fm_risk * 1_000_000

    return {
        'contract_id': contract_id,
        'fm_trigger_probability': round(fm_risk, 4),
        'triggered_by_events': triggered_events[:5],
        'financial_exposure_usd': round(financial_exposure, 2),
        'suggested_actions': _get_suggested_actions(triggered_events),
        'last_updated': datetime.utcnow().isoformat(),
    }


def _get_suggested_actions(triggered_events: List[Dict]) -> List[str]:
    actions = []
    types = {e.get('event_type') for e in triggered_events}
    if 'war' in types or 'sanctions' in types:
        actions.append('Review FM clause for war/sanctions coverage')
        actions.append('Activate alternative shipping route')
        actions.append('Contact war risk insurer')
    if 'port_closure' in types:
        actions.append('Identify alternative ports and logistics routes')
    if 'natural_disaster' in types:
        actions.append('Check supplier locations against disaster zone')
    if 'pandemic' in types:
        actions.append('Review labor supply and border crossing restrictions')
    if 'energy_shortage' in types:
        actions.append('Assess energy backup provisions in contract')
    return actions[:5]


# ─── Helper functions ─────────────────────────────────────────────────────────

def classify_fm_event(text: str):
    """
    Classify text into FM event type and return (event_type, risk_score).
    Returns (None, 0) if not FM-relevant.
    """
    text_lower = text.lower()
    best_type = None
    best_score = 0.0
    best_hits = 0

    for event_type, keywords in FM_CLASSIFIER.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > best_hits:
            best_hits = hits
            best_type = event_type
            best_score = min(0.95, 0.3 + hits * 0.15)

    if best_hits == 0:
        return None, 0.0
    return best_type, round(best_score, 2)


def detect_region(text: str) -> Optional[Dict]:
    """Detect the geographic region mentioned in text."""
    text_lower = text.lower()
    for region_key, region_data in RISK_REGIONS.items():
        if region_key in text_lower or region_data['country'].lower() in text_lower:
            return region_data
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# BALTIC DRY INDEX — FRED API (free, no key required)
# ═══════════════════════════════════════════════════════════════════════════════
CACHE_TTL_BALTIC = 86400  # 24h

def fetch_baltic_dry_index() -> dict:
    """
    Fetches the Baltic Dry Index (BDI) from FRED.
    BDI < 1000 → shipping disruption signal.
    Cached for 24 hours.
    """
    cache_key = 'fm_baltic_dry_index'
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DBDIDY01'
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        lines = resp.text.strip().split('\n')
        # CSV: DATE,VALUE — filter out missing values ('.')
        data_rows = []
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) == 2 and parts[1].strip() != '.':
                try:
                    data_rows.append((parts[0].strip(), float(parts[1].strip())))
                except ValueError:
                    continue

        if not data_rows:
            raise ValueError('No BDI data rows found')

        current_date, current_bdi = data_rows[-1]
        # 30-day trend: compare last vs 30-row-ago
        bdi_30d_ago = data_rows[-30][1] if len(data_rows) >= 30 else data_rows[0][1]
        trend_pct = round((current_bdi - bdi_30d_ago) / max(bdi_30d_ago, 1) * 100, 1)

        # FM signal
        if current_bdi < 600:
            signal_strength = 'CRITICAL'
            shipping_disruption_prob = 0.85
        elif current_bdi < 1000:
            signal_strength = 'HIGH'
            shipping_disruption_prob = 0.65
        elif current_bdi < 1500:
            signal_strength = 'ELEVATED'
            shipping_disruption_prob = 0.40
        elif current_bdi < 2500:
            signal_strength = 'NORMAL'
            shipping_disruption_prob = 0.20
        else:
            signal_strength = 'BOOMING'
            shipping_disruption_prob = 0.10

        result = {
            'current_bdi': current_bdi,
            'current_date': current_date,
            'bdi_30d_ago': bdi_30d_ago,
            'bdi_30d_trend_pct': trend_pct,
            'trend_direction': 'UP' if trend_pct > 2 else 'DOWN' if trend_pct < -2 else 'FLAT',
            'fm_signal_strength': signal_strength,
            'implied_shipping_disruption_prob': shipping_disruption_prob,
            'interpretation': (
                'Extremely low BDI signals severe global shipping contraction — high FM risk.'
                if signal_strength == 'CRITICAL' else
                'Low BDI indicates reduced shipping demand — elevated supply chain FM risk.'
                if signal_strength == 'HIGH' else
                'BDI slightly below average — monitor for further decline.'
                if signal_strength == 'ELEVATED' else
                'BDI in normal range — shipping markets functioning.'
                if signal_strength == 'NORMAL' else
                'High BDI reflects strong shipping demand — low disruption risk.'
            ),
            'source': 'FRED / Baltic Exchange via Federal Reserve Economic Data',
            'recent_values': [(d, v) for d, v in data_rows[-10:]],
        }
        cache.set(cache_key, result, CACHE_TTL_BALTIC)
        return result

    except Exception as exc:
        logger.warning('Baltic Dry fetch failed: %s', exc)
        # Fallback mock
        return {
            'current_bdi': 1250,
            'current_date': 'N/A',
            'bdi_30d_ago': 1300,
            'bdi_30d_trend_pct': -3.8,
            'trend_direction': 'DOWN',
            'fm_signal_strength': 'ELEVATED',
            'implied_shipping_disruption_prob': 0.40,
            'interpretation': 'BDI data unavailable — using fallback estimate.',
            'source': 'fallback',
            'recent_values': [],
        }
