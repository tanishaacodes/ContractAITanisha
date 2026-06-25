"""
Enterprise Risk Intelligence - Business Logic Services
Monte Carlo Simulations, GBM Forecasting, Risk Calculations
"""
import numpy as np
from decimal import Decimal
from typing import Dict, List, Tuple
from core.models import Contract
from .models import Supplier, Commodity, GeoPoliticalRisk, MonteCarloSimulation


class MonteCarloService:
    """Monte Carlo VaR simulation service"""

    @staticmethod
    def _calculate_contract_risk_parameters(contract: Contract) -> Tuple[float, float]:
        """
        Calculate dynamic volatility and drift based on contract-specific risk factors

        Args:
            contract: Contract object

        Returns:
            Tuple of (volatility, drift)
        """
        from .models import ContractSupplier, ContractCommodity, GeoPoliticalRisk

        # Base volatility (30% for medium risk contracts)
        base_volatility = 0.30

        # 1. Adjust for contract liability level
        liability_multipliers = {
            'LOW': 0.7,      # 70% of base = 21% volatility
            'MEDIUM': 1.0,   # 100% of base = 30% volatility
            'HIGH': 1.4,     # 140% of base = 42% volatility
        }
        liability_factor = liability_multipliers.get(contract.liability_level or 'MEDIUM', 1.0)

        # 2. Calculate supplier risk factor
        contract_suppliers = ContractSupplier.objects.filter(contract=contract).select_related('supplier')
        supplier_risk_avg = 0.5  # default medium risk
        if contract_suppliers.exists():
            risk_scores = [cs.supplier.risk_score for cs in contract_suppliers]
            supplier_risk_avg = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5

        # Single-source suppliers increase volatility
        single_source_count = sum(1 for cs in contract_suppliers if cs.supplier.is_single_source)
        single_source_penalty = min(single_source_count * 0.05, 0.15)  # Up to +15%

        # 3. Calculate commodity volatility factor
        contract_commodities = ContractCommodity.objects.filter(contract=contract).select_related('commodity')
        commodity_volatility_avg = 0.0
        if contract_commodities.exists():
            # Weight commodity volatility by value
            total_commodity_value = sum(float(cc.total_value) for cc in contract_commodities)
            if total_commodity_value > 0:
                weighted_vol = sum(
                    cc.commodity.volatility * float(cc.total_value)
                    for cc in contract_commodities
                )
                commodity_volatility_avg = weighted_vol / total_commodity_value

        # 4. Calculate geopolitical risk factor
        geo_risk_factor = 0.0
        if contract_suppliers.exists():
            supplier_countries = [cs.supplier.country for cs in contract_suppliers]
            geo_risks = GeoPoliticalRisk.objects.filter(country__in=supplier_countries)
            if geo_risks.exists():
                # High instability (low stability score) increases volatility
                avg_instability = sum(1 - gr.political_stability_score for gr in geo_risks) / len(geo_risks)
                geo_risk_factor = avg_instability * 0.10  # Up to +10%

                # Sanctions add significant risk
                sanction_count = sum(1 for gr in geo_risks if gr.has_active_sanctions)
                if sanction_count > 0:
                    geo_risk_factor += sanction_count * 0.08  # +8% per sanctioned country

        # Calculate final volatility
        volatility = base_volatility * liability_factor
        volatility += supplier_risk_avg * 0.15  # Supplier risk contributes up to 15%
        volatility += single_source_penalty
        volatility += commodity_volatility_avg * 0.3  # Commodity vol contributes 30%
        volatility += geo_risk_factor

        # Cap volatility between 15% and 80%
        volatility = max(0.15, min(0.80, volatility))

        # Calculate drift (expected return adjustment)
        # Higher risk contracts have negative drift (expected losses)
        base_drift = 0.0

        # Adjust drift based on risk factors
        if contract.liability_level == 'HIGH':
            base_drift -= 0.05  # -5% expected drift for high risk
        elif contract.liability_level == 'LOW':
            base_drift += 0.02  # +2% expected drift for low risk

        # Supplier risk affects drift
        base_drift -= (supplier_risk_avg - 0.5) * 0.10

        # Geopolitical risk affects drift
        base_drift -= geo_risk_factor * 0.5

        # Cap drift between -15% and +5%
        drift = max(-0.15, min(0.05, base_drift))

        return volatility, drift

    @staticmethod
    def _calculate_insurance_offset(contract: Contract) -> float:
        """
        Calculate total insurance coverage that offsets contract liability

        Args:
            contract: Contract object

        Returns:
            Total insurance coverage amount
        """
        try:
            # Import here to avoid circular imports
            from .models import InsurancePolicy

            # Get active insurance policies for this contract
            active_policies = InsurancePolicy.objects.filter(
                contract=contract,
                status='ACTIVE'
            )

            total_coverage = 0.0

            for policy in active_policies:
                # Check if policy is currently active (within date range)
                if policy.is_active:
                    # Use net coverage (coverage - deductible)
                    total_coverage += float(policy.net_coverage)

            return total_coverage

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Insurance offset calculation failed: {e}')
            return 0.0

    @staticmethod
    def run_simulation(contract_id: str, iterations: int = 30000) -> Dict:
        """
        Run Monte Carlo simulation for contract VaR analysis

        Args:
            contract_id: Contract ID
            iterations: Number of simulation iterations

        Returns:
            Dictionary with simulation results
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            contract = Contract.objects.get(id=contract_id)
            logger.info(f'[MonteCarloService] Retrieved contract: {contract.id}, filename={contract.original_filename}')
        except Contract.DoesNotExist:
            logger.error(f'[MonteCarloService] Contract not found: {contract_id}')
            raise
        except Exception as e:
            logger.error(f'[MonteCarloService] Error retrieving contract {contract_id}: {e}')
            raise

        # Get contract value (base exposure)
        base_exposure = float(contract.total_liability) if contract.total_liability else 100000000.0

        # Calculate insurance offsets
        insurance_coverage = MonteCarloService._calculate_insurance_offset(contract)
        net_exposure = base_exposure - insurance_coverage

        logger.info(f'[MonteCarloService] Base exposure: {base_exposure}, Insurance coverage: {insurance_coverage}, Net exposure: {net_exposure}')

        # Calculate dynamic risk parameters based on contract-specific data
        volatility, drift = MonteCarloService._calculate_contract_risk_parameters(contract)
        time_horizon = 1.0  # 1 year

        logger.info(f'[MonteCarloService] Dynamic volatility: {volatility:.3f}, drift: {drift:.3f}')

        # Generate random scenarios (seed from contract_id for reproducible but contract-unique results)
        seed = int(abs(hash(contract_id)) % (2**31))
        np.random.seed(seed)
        random_shocks = np.random.normal(0, 1, iterations)

        # Calculate exposure for each scenario (using net exposure after insurance)
        exposures = net_exposure * np.exp(
            (drift - 0.5 * volatility ** 2) * time_horizon +
            volatility * np.sqrt(time_horizon) * random_shocks
        )

        # Calculate statistics
        mean_exposure = float(np.mean(exposures))
        median_exposure = float(np.median(exposures))
        std_dev = float(np.std(exposures))
        min_exposure = float(np.min(exposures))
        max_exposure = float(np.max(exposures))

        # Calculate VaR percentiles
        var_90 = float(np.percentile(exposures, 90))
        var_95 = float(np.percentile(exposures, 95))
        var_99 = float(np.percentile(exposures, 99))

        # Calculate CVaR (Expected Shortfall)
        cvar_95 = float(np.mean(exposures[exposures >= var_95]))
        cvar_99 = float(np.mean(exposures[exposures >= var_99]))

        # Generate distribution histogram
        hist, bin_edges = np.histogram(exposures, bins=50)
        distribution_data = [
            {
                'exposure': float((bin_edges[i] + bin_edges[i + 1]) / 2 / 1_000_000),  # In millions
                'frequency': int(hist[i])
            }
            for i in range(len(hist))
        ]

        # Generate convergence data (running mean)
        convergence_points = 100
        step = iterations // convergence_points
        convergence_data = [
            {
                'iteration': i * step,
                'mean': float(np.mean(exposures[:i * step]))
            }
            for i in range(1, convergence_points + 1)
        ]

        # Store simulation results (best-effort — don't fail if DB write fails)
        try:
            MonteCarloSimulation.objects.create(
                contract=contract,
                iterations=iterations,
                mean_exposure=Decimal(str(round(mean_exposure, 2))),
                median_exposure=Decimal(str(round(median_exposure, 2))),
                std_dev=Decimal(str(round(std_dev, 2))),
                var_90=Decimal(str(round(var_90, 2))),
                var_95=Decimal(str(round(var_95, 2))),
                var_99=Decimal(str(round(var_99, 2))),
                cvar_95=Decimal(str(round(cvar_95, 2))),
                cvar_99=Decimal(str(round(cvar_99, 2))),
                min_exposure=Decimal(str(round(min_exposure, 2))),
                max_exposure=Decimal(str(round(max_exposure, 2))),
                distribution_data=distribution_data,
                convergence_data=convergence_data
            )
        except Exception as db_err:
            import logging
            logging.getLogger(__name__).warning(f'Monte Carlo DB write failed (non-fatal): {db_err}')

        # Get risk factor details for transparency
        from .models import ContractSupplier, ContractCommodity
        supplier_count = ContractSupplier.objects.filter(contract=contract).count()
        commodity_count = ContractCommodity.objects.filter(contract=contract).count()
        single_source_count = ContractSupplier.objects.filter(
            contract=contract, supplier__is_single_source=True
        ).count()

        return {
            'iterations': iterations,
            'mean': mean_exposure,
            'median': median_exposure,
            'std_dev': std_dev,
            'p90': var_90,
            'p95': var_95,
            'p99': var_99,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'min': min_exposure,
            'max': max_exposure,
            'distribution': distribution_data,
            'convergence': convergence_data,
            'risk_parameters': {
                'volatility': round(volatility, 4),
                'drift': round(drift, 4),
                'base_exposure': base_exposure,
                'insurance_coverage': insurance_coverage,
                'net_exposure': net_exposure,
                'liability_level': contract.liability_level or 'MEDIUM',
                'supplier_count': supplier_count,
                'commodity_count': commodity_count,
                'single_source_suppliers': single_source_count,
            }
        }


class CommodityForecastService:
    """Geometric Brownian Motion commodity price forecasting"""

    @staticmethod
    def generate_gbm_forecast(
        commodity_name: str,
        horizon_days: int = 252,
        num_paths: int = 1,
        volatility_adjustment: float = 0.0,
        drift_adjustment: float = 0.0,
        override_exposure: float = None,
        contract_id: str = '',
    ) -> Dict:
        """
        Generate contract-specific commodity price forecast using GBM.

        Args:
            commodity_name:       Commodity name (e.g., 'Steel', 'Copper')
            horizon_days:         Forecast horizon in trading days (default 252 = 1 year)
            num_paths:            Number of simulation paths
            volatility_adjustment: Extra volatility from contract risk factors
            drift_adjustment:     Drift adjustment from contract risk factors
            override_exposure:    Contract-specific exposure (overrides commodity.total_exposure)

        Returns:
            Dictionary with forecast data
        """
        try:
            commodity = Commodity.objects.get(name=commodity_name)
        except Commodity.DoesNotExist:
            commodity = type('obj', (object,), {
                'current_price': Decimal('800'),
                'volatility': 0.3,
                'drift': 0.05,
                'total_exposure': Decimal('12000000')
            })()

        current_price = float(commodity.current_price)
        # Apply contract-specific adjustments to base commodity params
        sigma = max(0.05, min(0.95, commodity.volatility + volatility_adjustment))
        mu    = max(-0.20, min(0.30, commodity.drift + drift_adjustment))

        # Use contract-specific exposure if provided, else fall back to commodity total
        # Ensure a minimum of ₹10M so Risk Impact is never zero
        fallback_exposure = max(float(commodity.total_exposure), 10_000_000)
        exposure = override_exposure if override_exposure is not None else fallback_exposure

        dt = 1 / horizon_days

        # Use contract_id-seeded random so different contracts get different paths
        seed_str = commodity_name + str(round(volatility_adjustment, 4)) + contract_id
        seed = int(abs(hash(seed_str)) % (2**31))
        np.random.seed(seed)

        prices      = [current_price]
        upper_band  = [current_price]
        lower_band  = [current_price]

        for _ in range(1, horizon_days + 1):
            shock      = np.random.normal(0, 1)
            prev       = prices[-1]
            next_price = prev * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock)
            upper      = prev * np.exp((mu + sigma) * dt)
            lower      = prev * np.exp((mu - sigma) * dt)
            prices.append(next_price)
            upper_band.append(upper)
            lower_band.append(lower)

        forecast = [
            {'day': i, 'price': round(float(prices[i]), 2),
             'upper': round(float(upper_band[i]), 2),
             'lower': round(float(lower_band[i]), 2)}
            for i in range(len(prices))
        ]

        expected_price   = prices[-1]
        max_price        = max(prices)
        min_price        = min(prices)
        price_change_pct = ((expected_price - current_price) / current_price) * 100
        risk_impact      = exposure * sigma

        # Scenario analysis — vary volatility around the contract-adjusted sigma
        scenarios = [
            {'scenario': 'Low Vol',    'price': round(current_price * np.exp((mu - sigma * 0.5) * 1.0), 2), 'probability': 0.25, 'volatility': round(sigma * 0.7, 3)},
            {'scenario': 'Base Case',  'price': round(current_price * np.exp(mu * 1.0), 2),                  'probability': 0.50, 'volatility': round(sigma, 3)},
            {'scenario': 'High Vol',   'price': round(current_price * np.exp((mu - sigma * 1.5) * 1.0), 2),  'probability': 0.15, 'volatility': round(sigma * 1.5, 3)},
            {'scenario': 'Stress',     'price': round(current_price * np.exp((mu - sigma * 2.5) * 1.0), 2),  'probability': 0.10, 'volatility': round(sigma * 2.0, 3)},
        ]

        return {
            'commodity':          commodity_name,
            'current_price':      current_price,
            'forecast_horizon':   '1 Year',
            'volatility':         round(sigma, 4),
            'base_volatility':    round(commodity.volatility, 4),
            'volatility_adj':     round(volatility_adjustment, 4),
            'drift':              round(mu, 4),
            'base_drift':         round(commodity.drift, 4),
            'drift_adj':          round(drift_adjustment, 4),
            'contract_exposure':  round(exposure, 2),
            'forecast':           forecast,
            'expected_price':     round(expected_price, 2),
            'max_price':          round(max_price, 2),
            'min_price':          round(min_price, 2),
            'price_change_percent': round(price_change_pct, 2),
            'risk_impact':        round(risk_impact, 2),
            'volatility_scenarios': scenarios,
        }


class KnowledgeGraphService:
    """Contract knowledge graph construction"""

    @staticmethod
    def build_contract_graph(contract_id: str) -> Dict:
        """
        Build knowledge graph for a contract.
        Combines DB relations + clause/text extraction for rich graphs.
        """
        import re
        contract = Contract.objects.get(id=contract_id)

        nodes = []
        edges = []
        node_ids = set()

        def add_node(node):
            if node['id'] not in node_ids:
                node_ids.add(node['id'])
                nodes.append(node)

        contract_value = float(contract.total_liability) if contract.total_liability else 100_000_000
        contract_node_id = f'contract-{contract.id}'
        add_node({
            'id': contract_node_id,
            'label': (contract.original_filename or contract.filename or 'Contract')[:30],
            'type': 'Contract',
            'value': f'₹{contract_value / 1_000_000:.1f}M'
        })

        # ── DB-linked suppliers ──────────────────────────────────────────
        try:
            contract_suppliers = contract.contract_suppliers.select_related('supplier').all()
            for cs in contract_suppliers:
                supplier = cs.supplier
                sid = f'supplier-{supplier.id}'
                add_node({'id': sid, 'label': supplier.name, 'type': 'Supplier', 'risk': supplier.risk_level})
                edges.append({'source': contract_node_id, 'target': sid, 'label': 'DEPENDS_ON'})

                cid = f'country-{supplier.country.replace(" ", "_")}'
                add_node({'id': cid, 'label': supplier.country, 'type': 'Country', 'stability': supplier.political_stability_index})
                edges.append({'source': sid, 'target': cid, 'label': 'LOCATED_IN'})

                try:
                    geo_risk = GeoPoliticalRisk.objects.get(country=supplier.country)
                    rid = f'geo-risk-{geo_risk.id}'
                    add_node({'id': rid, 'label': f'{geo_risk.risk_severity} Risk', 'type': 'GeoPoliticalRisk', 'severity': geo_risk.risk_severity})
                    edges.append({'source': cid, 'target': rid, 'label': 'HAS_GEO_RISK'})
                    if geo_risk.has_active_sanctions:
                        sanid = f'sanction-{geo_risk.id}'
                        add_node({'id': sanid, 'label': 'Trade Sanctions', 'type': 'Sanction', 'active': True})
                        edges.append({'source': cid, 'target': sanid, 'label': 'HAS_SANCTION'})
                except GeoPoliticalRisk.DoesNotExist:
                    pass
        except Exception:
            pass

        # ── DB-linked commodities ────────────────────────────────────────
        try:
            for cc in contract.contract_commodities.select_related('commodity').all():
                commodity = cc.commodity
                comid = f'commodity-{commodity.id}'
                add_node({'id': comid, 'label': commodity.name, 'type': 'Commodity', 'volatility': commodity.volatility})
                edges.append({'source': contract_node_id, 'target': comid, 'label': 'USES_COMMODITY'})
        except Exception:
            pass

        # ── DB liability node ────────────────────────────────────────────
        if contract.total_liability:
            lid = f'liability-{contract.id}'
            add_node({'id': lid, 'label': f'₹{float(contract.total_liability) / 1_000_000:.1f}M Liability', 'type': 'Liability', 'amount': f'₹{float(contract.total_liability) / 1_000_000:.1f}M'})
            edges.append({'source': contract_node_id, 'target': lid, 'label': 'HAS_LIABILITY'})

        # ── Text-extracted enrichment (always runs) ──────────────────────
        text = (getattr(contract, 'full_text', '') or '').lower()

        # Parties from DB fields — skip generic/placeholder values
        skip_party = {'not specified', 'the parties', 'supersedes', 'party a', 'party b', ''}
        for field, label in [('party_a', contract.party_a), ('party_b', contract.party_b)]:
            if label and label.strip().lower() not in skip_party and len(label.strip()) > 3:
                pid = f'party-{field}'
                add_node({'id': pid, 'label': label[:25], 'type': 'Supplier'})
                edges.append({'source': contract_node_id, 'target': pid, 'label': 'DEPENDS_ON'})

        # Jurisdiction → Country node
        jurisdiction = getattr(contract, 'jurisdiction', None)
        if jurisdiction and jurisdiction.strip().lower() not in {'not specified', 'unknown', '', 'n/a'}:
            jid = f'country-{jurisdiction.replace(" ", "_")}'
            add_node({'id': jid, 'label': jurisdiction, 'type': 'Country', 'stability': 7.0})
            edges.append({'source': contract_node_id, 'target': jid, 'label': 'LOCATED_IN'})

        # Liability clause node from text
        if 'liability' in text or 'indemnif' in text:
            lid2 = f'liability-clause-{contract.id}'
            level = getattr(contract, 'liability_level', 'MEDIUM') or 'MEDIUM'
            add_node({'id': lid2, 'label': f'{level} Liability', 'type': 'Liability', 'amount': level})
            if lid2 not in {e['target'] for e in edges}:
                edges.append({'source': contract_node_id, 'target': lid2, 'label': 'HAS_LIABILITY'})

        # Clauses → Risk nodes
        try:
            from core.models import Clause
            clauses = Clause.objects.filter(contract=contract, found=True).values('clause_name', 'extracted_text')[:8]
            for clause in clauses:
                name = clause['clause_name'] or 'Clause'
                cid = f'clause-{name.replace(" ", "_")}-{contract.id}'
                risk_keywords = ['terminat', 'liabil', 'penalty', 'breach', 'force majeure', 'indemni', 'arbitrat']
                is_risk = any(k in (clause['extracted_text'] or '').lower() for k in risk_keywords)
                add_node({
                    'id': cid,
                    'label': name[:20],
                    'type': 'GeoPoliticalRisk' if is_risk else 'Commodity',
                    'severity': 'HIGH' if is_risk else 'LOW'
                })
                edges.append({'source': contract_node_id, 'target': cid, 'label': 'HAS_GEO_RISK' if is_risk else 'USES_COMMODITY'})
        except Exception:
            pass

        # Geo keywords → GeoPoliticalRisk nodes
        geo_keywords = {
            'russia': 'Russia', 'china': 'China', 'iran': 'Iran',
            'ukraine': 'Ukraine', 'middle east': 'Middle East',
            'india': 'India', 'usa': 'USA', 'united states': 'USA',
            'europe': 'Europe', 'africa': 'Africa',
        }
        for kw, label in geo_keywords.items():
            if kw in text:
                gid = f'geo-kw-{label.replace(" ", "_")}'
                cid = f'country-kw-{label.replace(" ", "_")}'
                add_node({'id': cid, 'label': label, 'type': 'Country', 'stability': 5.0})
                edges.append({'source': contract_node_id, 'target': cid, 'label': 'LOCATED_IN'})
                if any(w in text for w in ['sanction', 'embargo', 'restrict']):
                    add_node({'id': gid, 'label': f'{label} Risk', 'type': 'GeoPoliticalRisk', 'severity': 'HIGH'})
                    edges.append({'source': cid, 'target': gid, 'label': 'HAS_GEO_RISK'})

        # Commodity keywords
        commodity_keywords = {
            'steel': 'Steel', 'concrete': 'Concrete', 'software': 'Software',
            'hardware': 'Hardware', 'oil': 'Oil', 'gas': 'Gas',
            'copper': 'Copper', 'labour': 'Labour', 'equipment': 'Equipment',
        }
        for kw, label in commodity_keywords.items():
            if kw in text:
                comid2 = f'commodity-kw-{label}'
                add_node({'id': comid2, 'label': label, 'type': 'Commodity', 'volatility': 0.3})
                edges.append({'source': contract_node_id, 'target': comid2, 'label': 'USES_COMMODITY'})

        return {'nodes': nodes, 'edges': edges}
