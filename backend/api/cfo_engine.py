"""
CFO Contract-Aware Financial Intelligence Engine
=================================================
Advanced Monte Carlo simulation with contract structure awareness,
time-series modeling, cascading scenario analysis, and decision intelligence.
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field


# ─── Contract Parameters ──────────────────────────────────────────────────────

@dataclass
class ContractParameters:
    """Parsed contract financial structure."""
    contract_value: float
    duration_months: int = 12
    payment_terms_days: int = 30       # net-30, net-60, etc.
    penalty_rate_daily: float = 0.001  # 0.1% of contract value per delay day
    max_penalty_cap: float = 0.10      # maximum 10% of contract value
    cost_base_ratio: float = 0.70      # 70% cost, 30% margin baseline
    currency: str = "USD"
    delay_probability: float = 0.25    # 25% chance a delay event occurs
    avg_delay_days: float = 30.0       # average delay days when triggered


# ─── Contract Financial Model ─────────────────────────────────────────────────

class ContractFinancialModel:
    """
    Builds a structured financial model from contract parameters.
    Computes revenue schedule, cost structure, penalty risks, and delay impact.
    """

    def __init__(self, params: ContractParameters):
        self.p = params
        self.monthly_revenue = params.contract_value / max(params.duration_months, 1)
        self.monthly_cost_base = self.monthly_revenue * params.cost_base_ratio
        self.max_penalty = params.contract_value * params.max_penalty_cap

    def revenue_schedule(self) -> List[Dict]:
        """Month-by-month revenue schedule accounting for payment delay."""
        schedule = []
        payment_delay_months = self.p.payment_terms_days / 30.0
        for m in range(1, self.p.duration_months + 1):
            cash_received = self.monthly_revenue if m > payment_delay_months else 0.0
            schedule.append({
                "month": m,
                "earned": round(self.monthly_revenue, 2),
                "cash_received": round(cash_received, 2),
            })
        return schedule

    def penalty_exposure(self, delay_days: float) -> float:
        """Calculate penalty cost for a given delay in days (capped)."""
        penalty = delay_days * self.p.penalty_rate_daily * self.p.contract_value
        return min(penalty, self.max_penalty)

    def delay_total_impact(self, delay_days: float) -> float:
        """Total financial impact of delay: penalty + idle overhead costs."""
        penalty = self.penalty_exposure(delay_days)
        daily_fixed_cost = self.monthly_cost_base / 30.0 * 0.30  # 30% fixed overhead
        return penalty + (delay_days * daily_fixed_cost)


# ─── Advanced Monte Carlo Engine ──────────────────────────────────────────────

class MonteCarloEngine:
    """
    Correlated Monte Carlo simulation engine.
    Uses Cholesky decomposition for realistic co-movement between oil, inflation, FX.
    Tracks margin distribution, VaR, penalty exposure, and delay rates.
    """

    def __init__(self, params: ContractParameters, n_sims: int = 2000, seed: int = 42):
        self.model = ContractFinancialModel(params)
        self.p = params
        self.n = n_sims
        self.rng = np.random.default_rng(seed)

    def run(self, oil_shock: float = 0.0, inflation: float = 0.0, fx_shock: float = 0.0) -> Dict:
        """
        Full Monte Carlo run. Returns margin distribution, penalty stats, VaR, histogram.
        """
        p = self.p
        n = self.n

        # Correlated shock matrix: oil & inflation correlate ~0.6, FX mild correlation
        corr = np.array([
            [1.00, 0.60, 0.10],
            [0.60, 1.00, 0.20],
            [0.10, 0.20, 1.00],
        ])
        L = np.linalg.cholesky(corr)
        z = self.rng.standard_normal((3, n))
        cz = L @ z  # correlated standard normals

        # Per-shock volatility bands
        oil_vol = max(abs(oil_shock) * 0.30, 0.02)
        inf_vol = max(abs(inflation) * 0.25, 0.015)
        fx_vol  = max(abs(fx_shock) * 0.35, 0.01)

        sim_oil = oil_shock + cz[0] * oil_vol
        sim_inf = inflation  + cz[1] * inf_vol
        sim_fx  = fx_shock   + cz[2] * fx_vol

        # Simulated cost with compounding macro shocks
        base_cost = p.contract_value * p.cost_base_ratio
        sim_cost = base_cost * (
            (1 + sim_oil * 0.05) *
            (1 + sim_inf * 0.10) *
            (1 + np.abs(sim_fx) * 0.07)
        )

        # Probabilistic delay events
        delay_hit  = self.rng.random(n) < p.delay_probability
        delay_days = np.where(delay_hit, self.rng.exponential(p.avg_delay_days, n), 0.0)
        penalty_costs = np.array([self.model.penalty_exposure(d) for d in delay_days])
        idle_costs    = delay_days * (self.model.monthly_cost_base / 30.0) * 0.30

        # Revenue eroded by FX
        revenue = p.contract_value * (1.0 - np.abs(sim_fx) * 0.04)

        total_cost = sim_cost + penalty_costs + idle_costs
        margin_pct = (revenue - total_cost) / np.maximum(revenue, 1e-6) * 100.0

        # ── Statistics ──
        mean_m  = float(np.mean(margin_pct))
        std_m   = float(np.std(margin_pct))
        p1_m    = float(np.percentile(margin_pct, 1))
        p99_m   = float(np.percentile(margin_pct, 99))
        var_95  = float(np.percentile(margin_pct, 5))   # 95% VaR
        es_95   = float(np.mean(margin_pct[margin_pct < var_95]))  # Expected Shortfall
        loss_pr = float(np.mean(margin_pct < 0)) * 100.0

        # ── Penalty stats ──
        mean_pen   = float(np.mean(penalty_costs))
        max_pen_p99 = float(np.percentile(penalty_costs, 99))
        delay_rate = float(np.mean(delay_hit)) * 100.0

        # ── Distribution histogram (30 bins) ──
        hist_counts, hist_bins = np.histogram(margin_pct, bins=30)
        distribution = [
            {"margin": round(float(hist_bins[i]), 2), "count": int(hist_counts[i])}
            for i in range(len(hist_counts))
        ]

        # ── 50-point sample for scatter chart ──
        idx = np.linspace(0, n - 1, 50, dtype=int)
        scenario_samples = [
            {"x": int(i), "margin": round(float(margin_pct[i]), 2)} for i in idx
        ]

        return {
            "summary": {
                "mean_margin":        round(mean_m,  2),
                "std_deviation":      round(std_m,   2),
                "min_margin":         round(p1_m,    2),
                "max_margin":         round(p99_m,   2),
                "loss_probability":   round(loss_pr, 2),
                "var_95":             round(var_95,  2),
                "expected_shortfall": round(es_95,   2),
            },
            "penalty": {
                "mean_penalty":        round(mean_pen,    2),
                "max_penalty_p99":     round(max_pen_p99, 2),
                "delay_rate":          round(delay_rate,  2),
                "penalty_cap":         round(p.contract_value * p.max_penalty_cap, 2),
            },
            "distribution":    distribution,
            "scenario_samples": scenario_samples,
        }


# ─── Time-Series Simulator ────────────────────────────────────────────────────

class TimeSeriesSimulator:
    """
    Month-by-month contract lifecycle simulation across multiple paths.
    Models cost escalation, payment delays, and delay event propagation.
    Returns mean cashflow timeline with confidence bands.
    """

    def __init__(self, params: ContractParameters, seed: int = 42):
        self.p = params
        self.model = ContractFinancialModel(params)
        self.rng = np.random.default_rng(seed)

    def simulate(
        self,
        oil_shock: float = 0.0,
        inflation: float = 0.0,
        fx_shock: float = 0.0,
        n_paths: int = 300,
    ) -> List[Dict]:
        """
        Returns month-by-month mean cashflow, cumulative P&L, and P10/P90 bands.
        """
        months = self.p.duration_months
        m_rev  = self.model.monthly_revenue
        m_cost = self.model.monthly_cost_base

        all_cf  = np.zeros((n_paths, months))
        all_cum = np.zeros((n_paths, months))
        all_mrg = np.zeros((n_paths, months))

        for path in range(n_paths):
            delay_hit   = self.rng.random() < self.p.delay_probability
            delay_month = int(self.rng.integers(1, months)) if delay_hit else -1
            delay_days  = float(self.rng.exponential(self.p.avg_delay_days)) if delay_hit else 0.0
            cumulative  = 0.0

            for m in range(months):
                mn = m + 1
                # Cost escalates with inflation (compounding) + oil noise
                inf_factor = (1 + inflation * 0.08) ** (mn / 12.0)
                oil_factor = 1.0 + oil_shock * 0.04 * (1.0 + self.rng.normal(0, 0.10))
                cost_m = m_cost * inf_factor * oil_factor

                # FX drift erodes revenue
                fx_drift = fx_shock * 0.03 * self.rng.normal(1, 0.15)
                rev_m = m_rev * (1.0 - abs(fx_drift) * 0.04)

                # Delay month: zero revenue + full penalty + idle cost
                if mn == delay_month:
                    impact = self.model.delay_total_impact(delay_days)
                    rev_m   = 0.0
                    cost_m += impact

                net = rev_m - cost_m
                cumulative += net
                margin_m = (net / max(rev_m, 1e-6)) * 100.0 if rev_m > 0 else -100.0

                all_cf[path, m]  = net
                all_cum[path, m] = cumulative
                all_mrg[path, m] = margin_m

        mean_cf  = np.mean(all_cf,  axis=0)
        p10_cf   = np.percentile(all_cf, 10, axis=0)
        p90_cf   = np.percentile(all_cf, 90, axis=0)
        mean_cum = np.mean(all_cum, axis=0)
        mean_mrg = np.mean(all_mrg, axis=0)

        return [
            {
                "month":           mn + 1,
                "cashflow":        round(float(mean_cf[mn]),  2),
                "cashflow_p10":    round(float(p10_cf[mn]),   2),
                "cashflow_p90":    round(float(p90_cf[mn]),   2),
                "cumulative":      round(float(mean_cum[mn]), 2),
                "margin_pct":      round(float(mean_mrg[mn]), 2),
            }
            for mn in range(months)
        ]


# ─── Cascading Scenario Definitions ──────────────────────────────────────────

SCENARIO_CASCADES = {
    "war": {
        "label": "War / Geopolitical Shock", "icon": "💥",
        "oil_shock": 0.35, "inflation": 0.18, "fx_shock": 0.12, "delay_multiplier": 2.5,
        "chain": [
            {"event": "Geopolitical conflict escalates",    "impact": "Supply routes disrupted"},
            {"event": "Oil price surge +30–50%",            "impact": "Production costs rise 15–25%"},
            {"event": "Delivery delays 45–90 days",         "impact": "Penalty clauses triggered"},
            {"event": "Penalty exposure activates",         "impact": "Margin erodes 8–18%"},
            {"event": "FX volatility spikes",               "impact": "Cross-border payment loss 5–12%"},
        ],
    },
    "pandemic": {
        "label": "Pandemic / Health Crisis", "icon": "🦠",
        "oil_shock": -0.15, "inflation": 0.10, "fx_shock": 0.08, "delay_multiplier": 1.8,
        "chain": [
            {"event": "Workforce disruptions begin",         "impact": "Productivity drops 20–35%"},
            {"event": "Supply chain constraints",            "impact": "Material costs up 10–20%"},
            {"event": "Demand shock (oil drops)",            "impact": "Energy costs decrease short-term"},
            {"event": "Regulatory lockdowns",               "impact": "Force majeure may activate"},
            {"event": "Payment delays increase",             "impact": "Cash flow gap widens 30–60 days"},
        ],
    },
    "inflation": {
        "label": "Hyperinflation Spiral", "icon": "📈",
        "oil_shock": 0.10, "inflation": 0.25, "fx_shock": 0.06, "delay_multiplier": 1.2,
        "chain": [
            {"event": "CPI spikes system-wide",              "impact": "Input costs rise 15–30%"},
            {"event": "Central bank rate hike",              "impact": "Financing costs increase"},
            {"event": "Labor cost escalation",               "impact": "Operational costs rise 10–20%"},
            {"event": "Renegotiation trigger activated",     "impact": "Contract terms disputed"},
            {"event": "Margin compression",                  "impact": "Profitability at risk without escalation clause"},
        ],
    },
    "supply_chain": {
        "label": "Supply Chain Disruption", "icon": "🚢",
        "oil_shock": 0.20, "inflation": 0.15, "fx_shock": 0.08, "delay_multiplier": 2.0,
        "chain": [
            {"event": "Port congestion / shipping delays",   "impact": "Lead times extend 30–60 days"},
            {"event": "Freight costs surge +40–80%",        "impact": "Logistics costs escalate"},
            {"event": "Material shortages",                  "impact": "Substitution costs up 15–25%"},
            {"event": "Delivery milestones missed",          "impact": "Penalty clauses triggered"},
            {"event": "Buyer demands renegotiation",         "impact": "Revenue at risk"},
        ],
    },
}


def run_scenario_cascade(params: ContractParameters, scenario_key: str, n_sims: int = 1000) -> Dict:
    """Compare baseline vs stressed scenario. Returns cascade chain + delta metrics."""
    sc = SCENARIO_CASCADES.get(scenario_key)
    if not sc:
        return {"error": f"Unknown scenario: {scenario_key}"}

    stressed_params = ContractParameters(
        contract_value=params.contract_value,
        duration_months=params.duration_months,
        payment_terms_days=params.payment_terms_days,
        penalty_rate_daily=params.penalty_rate_daily,
        max_penalty_cap=params.max_penalty_cap,
        cost_base_ratio=params.cost_base_ratio,
        currency=params.currency,
        delay_probability=min(params.delay_probability * sc["delay_multiplier"], 0.95),
        avg_delay_days=params.avg_delay_days * sc["delay_multiplier"],
    )

    baseline = MonteCarloEngine(params, n_sims).run(0, 0, 0)
    stressed = MonteCarloEngine(stressed_params, n_sims).run(
        sc["oil_shock"], sc["inflation"], sc["fx_shock"]
    )

    return {
        "scenario":       scenario_key,
        "label":          sc["label"],
        "icon":           sc["icon"],
        "cascade_chain":  sc["chain"],
        "baseline":       baseline["summary"],
        "stressed":       stressed["summary"],
        "delta": {
            "margin_change":    round(stressed["summary"]["mean_margin"]      - baseline["summary"]["mean_margin"],      2),
            "loss_prob_change": round(stressed["summary"]["loss_probability"] - baseline["summary"]["loss_probability"], 2),
            "penalty_increase": round(stressed["penalty"]["mean_penalty"]     - baseline["penalty"]["mean_penalty"],     2),
        },
        "stressed_penalty": stressed["penalty"],
    }


# ─── Decision Intelligence Layer ──────────────────────────────────────────────

def generate_risk_insights(
    params: ContractParameters,
    sim: Dict,
    oil_shock: float,
    inflation: float,
    fx_shock: float,
) -> List[Dict]:
    """
    Produce CFO-level actionable findings from simulation output.
    Each insight has: severity (CRITICAL/HIGH/MEDIUM/LOW), category, finding, recommendation.
    """
    insights: List[Dict] = []
    s = sim["summary"]
    p = sim["penalty"]

    # ── Margin health ──
    if s["mean_margin"] < 0:
        insights.append({
            "severity": "CRITICAL", "category": "Margin", "icon": "🚨",
            "finding": f"Expected margin is {s['mean_margin']:.1f}% — contract is loss-making under current shocks.",
            "recommendation": "Immediate renegotiation required. Add cost escalation clause tied to oil/CPI indices.",
        })
    elif s["mean_margin"] < 5:
        insights.append({
            "severity": "HIGH", "category": "Margin", "icon": "⚠️",
            "finding": f"Thin margin of {s['mean_margin']:.1f}% leaves near-zero buffer for cost overruns.",
            "recommendation": "Add price review trigger at ±10% macro shock. Switch to milestone-based invoicing.",
        })

    # ── Loss probability ──
    if s["loss_probability"] > 50:
        insights.append({
            "severity": "CRITICAL", "category": "Risk", "icon": "🚨",
            "finding": f"{s['loss_probability']:.0f}% of simulated outcomes result in loss.",
            "recommendation": "Do not proceed without hedging. Use FX forward contracts and supplier price locks.",
        })
    elif s["loss_probability"] > 25:
        insights.append({
            "severity": "HIGH", "category": "Risk", "icon": "⚠️",
            "finding": f"{s['loss_probability']:.0f}% loss probability exceeds 25% threshold.",
            "recommendation": "Strengthen force majeure clause. Cap liability at contract value percentage.",
        })
    elif s["loss_probability"] > 10:
        insights.append({
            "severity": "MEDIUM", "category": "Risk", "icon": "📊",
            "finding": f"{s['loss_probability']:.0f}% loss probability — manageable but worth monitoring.",
            "recommendation": "Add quarterly financial milestone reviews with renegotiation rights.",
        })

    # ── FX exposure ──
    if fx_shock > 0.08:
        insights.append({
            "severity": "HIGH", "category": "FX", "icon": "💱",
            "finding": f"FX shift of {fx_shock*100:.0f}% creates material cross-border payment exposure.",
            "recommendation": "Denominate payments in USD/EUR. Add FX hedging clause or forward rate locks.",
        })

    # ── Inflation exposure ──
    if inflation > 0.12:
        insights.append({
            "severity": "HIGH", "category": "Inflation", "icon": "📈",
            "finding": f"Inflation at {inflation*100:.0f}% will structurally erode cost margins over contract life.",
            "recommendation": "Add CPI-linked price escalation clause. Renegotiate material costs quarterly.",
        })

    # ── Penalty exposure ──
    pen_pct = (p["mean_penalty"] / params.contract_value * 100) if params.contract_value > 0 else 0
    if pen_pct > 3:
        insights.append({
            "severity": "HIGH", "category": "Penalties", "icon": "⚡",
            "finding": f"Average penalty exposure is {pen_pct:.1f}% of contract value (${p['mean_penalty']:,.0f}).",
            "recommendation": f"Add force majeure covering supply disruptions. Ensure penalty cap is at {params.max_penalty_cap*100:.0f}% of contract value.",
        })

    # ── Delay risk ──
    if p["delay_rate"] > 30:
        insights.append({
            "severity": "MEDIUM", "category": "Delays", "icon": "⏱️",
            "finding": f"{p['delay_rate']:.0f}% of simulations trigger delivery delays.",
            "recommendation": "Add 10–15% schedule buffer. Include milestone extension rights for force majeure events.",
        })

    # ── VaR tail risk ──
    if s["var_95"] < -10:
        insights.append({
            "severity": "HIGH", "category": "Tail Risk", "icon": "📉",
            "finding": f"95% VaR is {s['var_95']:.1f}% — worst-case tail scenarios show severe losses.",
            "recommendation": "Stress-test contract terms for black swan events. Verify insurance coverage.",
        })

    # ── All-clear ──
    if not insights:
        insights.append({
            "severity": "LOW", "category": "Overall", "icon": "✅",
            "finding": f"Contract financials are robust. Mean margin {s['mean_margin']:.1f}%, loss probability {s['loss_probability']:.1f}%.",
            "recommendation": "Maintain current structure. Consider a performance bonus clause to incentivize early delivery.",
        })

    return insights
