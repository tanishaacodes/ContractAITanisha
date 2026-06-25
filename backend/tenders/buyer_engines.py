"""
Buyer Bid Evaluation Engines
- Competitive Positioning Engine
- Bid Evolution Tracker
- AI Winner Recommendation Engine
- Legal Risk Weighted Ranking
- Collusion Detection Engine (price + clause similarity)
"""
import math
import random
from django.db.models import Min, Max, Avg, Count
from .models import VendorBid, VendorClause, TenderLegalMetadata

# ─────────────────────────────────────────────────────────────────────────────
# 1. COMPETITIVE POSITIONING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_competitive_metrics(tender_id):
    """
    For each vendor+round, computes:
    - price_gap_from_lowest
    - aggression_index  (0=least aggressive, 1=most)
    - positioning_score (weighted multi-factor)
    """
    bids = list(VendorBid.objects.filter(tender_id=tender_id).select_related('vendor'))
    if not bids:
        return []

    prices = [b.total_price for b in bids]
    lowest  = min(prices)
    highest = max(prices)
    avg     = sum(prices) / len(prices)
    spread  = highest - lowest or 1

    results = []
    for bid in bids:
        price_gap      = bid.total_price - lowest
        aggression_idx = (highest - bid.total_price) / spread          # 1 = lowest bidder
        price_score    = lowest / bid.total_price                       # 0-1

        positioning_score = (
            0.30 * (bid.technical_score  / 100) +
            0.25 * (bid.commercial_score / 100) +
            0.20 * price_score +
            0.10 * bid.vendor.financial_rating +
            0.10 * bid.vendor.past_performance_score -
            0.05 * bid.legal_risk_score
        )

        results.append({
            'vendor_id'             : bid.vendor_id,
            'vendor'                : bid.vendor.name,
            'round'                 : bid.round_number,
            'price'                 : bid.total_price,
            'price_gap_from_lowest' : price_gap,
            'aggression_index'      : round(aggression_idx, 4),
            'price_vs_avg'          : round((bid.total_price - avg) / avg * 100, 2),
            'technical_score'       : bid.technical_score,
            'commercial_score'      : bid.commercial_score,
            'legal_risk_score'      : bid.legal_risk_score,
            'positioning_score'     : round(positioning_score, 4),
        })

    results.sort(key=lambda x: x['positioning_score'], reverse=True)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 2. BID EVOLUTION TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def get_vendor_evolution(tender_id):
    """
    Returns per-vendor round-by-round trend:
    price, technical_score, risk trajectory.
    """
    bids = (VendorBid.objects
            .filter(tender_id=tender_id)
            .select_related('vendor')
            .order_by('vendor', 'round_number'))

    data = {}
    for bid in bids:
        vname = bid.vendor.name
        if vname not in data:
            data[vname] = {
                'vendor_id': bid.vendor_id,
                'rounds': [],
            }
        data[vname]['rounds'].append({
            'round'          : bid.round_number,
            'price'          : bid.total_price,
            'technical_score': bid.technical_score,
            'legal_risk'     : bid.legal_risk_score,
            'deviation'      : bid.deviation_score,
        })

    # Compute price delta per vendor
    for vname, info in data.items():
        rounds = info['rounds']
        if len(rounds) >= 2:
            first = rounds[0]['price']
            last  = rounds[-1]['price']
            info['price_delta_pct'] = round((last - first) / first * 100, 2)
        else:
            info['price_delta_pct'] = 0.0

    return data


# ─────────────────────────────────────────────────────────────────────────────
# 3. LEGAL RISK AGGREGATOR
# ─────────────────────────────────────────────────────────────────────────────

def compute_legal_risk(vendor_bid_id):
    """
    Aggregate clause-level deviation → legal_risk_score.
    Saves result back to VendorBid row.
    """
    try:
        bid = VendorBid.objects.get(id=vendor_bid_id)
    except VendorBid.DoesNotExist:
        return 0.0

    clauses = VendorClause.objects.filter(vendor_bid=bid)
    if not clauses.exists():
        return 0.0

    total_risk = sum(c.deviation_score * c.risk_score for c in clauses)
    normalized = total_risk / clauses.count()
    bid.legal_risk_score = round(normalized, 4)
    bid.save(update_fields=['legal_risk_score'])
    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# 4. AI WINNER RECOMMENDATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

WINNER_WEIGHTS = {
    'technical'   : 0.25,
    'commercial'  : 0.20,
    'legal'       : -0.15,
    'financial'   : 0.10,
    'performance' : 0.10,
    'price'       : 0.15,
    'delay'       : -0.05,
}


def recommend_winner(tender_id):
    """
    Produces multi-factor weighted ranking for buyer decision support.
    Returns list sorted by composite_score descending.
    """
    bids = list(VendorBid.objects.filter(tender_id=tender_id).select_related('vendor'))
    if not bids:
        return []

    # Use latest round per vendor
    latest = {}
    for bid in bids:
        vid = bid.vendor_id
        if vid not in latest or bid.round_number > latest[vid].round_number:
            latest[vid] = bid

    prices = [b.total_price for b in latest.values()]
    lowest = min(prices) if prices else 1

    ranking = []
    for bid in latest.values():
        price_score = lowest / bid.total_price   # higher is better

        composite = (
            WINNER_WEIGHTS['technical']   * (bid.technical_score  / 100) +
            WINNER_WEIGHTS['commercial']  * (bid.commercial_score / 100) +
            WINNER_WEIGHTS['legal']       * bid.legal_risk_score +
            WINNER_WEIGHTS['price']       * price_score +
            WINNER_WEIGHTS['delay']       * bid.delay_probability +
            WINNER_WEIGHTS['financial']   * bid.vendor.financial_rating +
            WINNER_WEIGHTS['performance'] * bid.vendor.past_performance_score
        )

        ranking.append({
            'vendor_id'      : bid.vendor_id,
            'vendor'         : bid.vendor.name,
            'round'          : bid.round_number,
            'price'          : bid.total_price,
            'technical_score': bid.technical_score,
            'commercial_score': bid.commercial_score,
            'legal_risk'     : bid.legal_risk_score,
            'delay_prob'     : bid.delay_probability,
            'financial_rating': bid.vendor.financial_rating,
            'performance'    : bid.vendor.past_performance_score,
            'composite_score': round(composite, 4),
            'score_breakdown': {
                'technical'  : round(WINNER_WEIGHTS['technical']   * bid.technical_score / 100, 4),
                'commercial' : round(WINNER_WEIGHTS['commercial']  * bid.commercial_score / 100, 4),
                'price'      : round(WINNER_WEIGHTS['price']       * price_score, 4),
                'legal_risk' : round(WINNER_WEIGHTS['legal']       * bid.legal_risk_score, 4),
                'financial'  : round(WINNER_WEIGHTS['financial']   * bid.vendor.financial_rating, 4),
                'performance': round(WINNER_WEIGHTS['performance'] * bid.vendor.past_performance_score, 4),
                'delay'      : round(WINNER_WEIGHTS['delay']       * bid.delay_probability, 4),
            },
        })

    ranking.sort(key=lambda x: x['composite_score'], reverse=True)

    # Assign rank and label
    for i, r in enumerate(ranking):
        r['rank'] = i + 1
        if i == 0:
            r['recommendation'] = 'RECOMMENDED WINNER'
        elif i == 1:
            r['recommendation'] = 'RESERVE BIDDER'
        else:
            r['recommendation'] = f'RANK {i+1}'

    return ranking


# ─────────────────────────────────────────────────────────────────────────────
# 5. COLLUSION DETECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def detect_price_collusion(tender_id, threshold=0.97):
    """
    Detect suspiciously similar round-by-round price vectors between vendors.
    Uses cosine similarity on price sequences.
    """
    bids = VendorBid.objects.filter(tender_id=tender_id).select_related('vendor').order_by('round_number')

    vendor_prices = {}
    for bid in bids:
        vname = bid.vendor.name
        vendor_prices.setdefault(vname, [])
        vendor_prices[vname].append(bid.total_price)

    vendors = list(vendor_prices.keys())
    suspicious = []

    for i in range(len(vendors)):
        for j in range(i + 1, len(vendors)):
            va, vb = vendors[i], vendors[j]
            pa, pb = vendor_prices[va], vendor_prices[vb]
            # Pad shorter vector
            max_len = max(len(pa), len(pb))
            pa += [pa[-1]] * (max_len - len(pa))
            pb += [pb[-1]] * (max_len - len(pb))

            sim = _cosine_similarity(pa, pb)
            if sim >= threshold:
                suspicious.append({
                    'vendor1'   : va,
                    'vendor2'   : vb,
                    'similarity': round(sim, 4),
                    'risk_level': 'CRITICAL' if sim > 0.99 else 'HIGH',
                    'reason'    : 'Near-identical price trajectories across rounds',
                })

    return suspicious


def detect_clause_collusion(tender_id, threshold=0.90):
    """
    Detect vendors submitting suspiciously similar clause texts.
    Uses character-level Jaccard similarity (no heavy ML dependency).
    """
    bids = (VendorBid.objects
            .filter(tender_id=tender_id)
            .prefetch_related('clauses')
            .select_related('vendor'))

    vendor_text = {}
    for bid in bids:
        vname = bid.vendor.name
        text  = ' '.join(c.clause_text for c in bid.clauses.all())
        vendor_text[vname] = text.lower()

    def jaccard(a, b):
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    vendors = list(vendor_text.keys())
    suspicious = []

    for i in range(len(vendors)):
        for j in range(i + 1, len(vendors)):
            va, vb = vendors[i], vendors[j]
            sim = jaccard(vendor_text[va], vendor_text[vb])
            if sim >= threshold:
                suspicious.append({
                    'vendor1'         : va,
                    'vendor2'         : vb,
                    'clause_similarity': round(sim, 4),
                    'risk_level'      : 'CRITICAL' if sim > 0.95 else 'HIGH',
                    'reason'          : 'Clause text vocabulary overlap above threshold',
                })

    return suspicious


# ─────────────────────────────────────────────────────────────────────────────
# 6. HEATMAP GENERATOR — clause deviation across vendors
# ─────────────────────────────────────────────────────────────────────────────

CLAUSE_TYPES = [
    'PAYMENT_TERMS', 'LIQUIDATED_DAMAGES', 'INDEMNITY',
    'LIABILITY', 'ARBITRATION', 'TERMINATION',
    'FORCE_MAJEURE', 'WARRANTY', 'GOVERNING_LAW',
    'PERFORMANCE_BOND',
]


def build_comparison_grid(tender_id):
    """
    Returns a grid: rows = clause_type, cols = vendor+round combos.
    Each cell has deviation_score (0-1) for heatmap colouring.
    """
    bids = list(VendorBid.objects.filter(tender_id=tender_id).select_related('vendor'))
    clauses = VendorClause.objects.filter(
        vendor_bid__tender_id=tender_id
    ).select_related('vendor_bid__vendor')

    # Build index: (vendor_bid_id, clause_type) → deviation_score
    clause_map = {}
    for c in clauses:
        clause_map[(c.vendor_bid_id, c.clause_type)] = c.deviation_score

    grid = []
    for ctype in CLAUSE_TYPES:
        row = {'clause_type': ctype, 'vendors': []}
        for bid in bids:
            dev = clause_map.get((bid.id, ctype), None)
            row['vendors'].append({
                'vendor'   : bid.vendor.name,
                'round'    : bid.round_number,
                'deviation': round(dev, 4) if dev is not None else None,
                'color'    : (
                    '#dc2626' if dev and dev > 0.5 else
                    '#f59e0b' if dev and dev > 0.2 else
                    '#16a34a' if dev is not None else '#374151'
                ),
            })
        grid.append(row)

    return grid


# ─────────────────────────────────────────────────────────────────────────────
# 7. MOCK DATA SEEDER  (for demo / testing)
# ─────────────────────────────────────────────────────────────────────────────

def seed_mock_bids(tender_id, num_vendors=5, num_rounds=3):
    """
    Seeds realistic mock vendors + bids for a given tender.
    Useful for demonstration without real bid submissions.
    """
    from .models import Vendor, VendorBid, VendorClause

    VENDOR_NAMES = [
        'Larsen & Toubro Infrastructure',
        'Tata Projects Limited',
        'Shapoorji Pallonji & Co',
        'Afcons Infrastructure',
        'NCC Limited',
        'HCC (Hindustan Construction)',
        'Simplex Infrastructures',
        'KEC International',
        'IRCON International',
        'ITD Cementation India',
    ]

    base_price = 5_000_000_000  # 500 Cr base

    seeded_vendors = []
    for i in range(min(num_vendors, len(VENDOR_NAMES))):
        vendor, _ = Vendor.objects.get_or_create(
            name=VENDOR_NAMES[i],
            defaults={
                'financial_rating'      : round(random.uniform(0.6, 0.95), 2),
                'past_performance_score': round(random.uniform(0.55, 0.90), 2),
            }
        )
        seeded_vendors.append(vendor)

    created_bids = []
    for vendor in seeded_vendors:
        price = base_price * random.uniform(0.88, 1.15)
        for rnd in range(1, num_rounds + 1):
            price = price * random.uniform(0.96, 1.01)   # minor round-to-round movement
            bid, created = VendorBid.objects.get_or_create(
                tender_id=tender_id,
                vendor=vendor,
                round_number=rnd,
                defaults={
                    'total_price'     : round(price, 2),
                    'technical_score' : round(random.uniform(60, 95), 1),
                    'commercial_score': round(random.uniform(55, 90), 1),
                    'legal_risk_score': round(random.uniform(0.1, 0.55), 2),
                    'delay_probability': round(random.uniform(0.05, 0.35), 2),
                    'deviation_score' : round(random.uniform(0.05, 0.45), 2),
                }
            )
            if created:
                # Seed a few clauses per bid
                for ctype in random.sample(CLAUSE_TYPES, k=4):
                    dev = round(random.uniform(0.02, 0.70), 2)
                    VendorClause.objects.get_or_create(
                        vendor_bid=bid,
                        clause_type=ctype,
                        defaults={
                            'clause_text'    : f"[Mock] Vendor proposes modified {ctype} terms.",
                            'deviation_score': dev,
                            'risk_score'     : round(dev * 0.9, 2),
                        }
                    )
            created_bids.append(bid)

    return {'vendors': len(seeded_vendors), 'bids': len(created_bids)}
