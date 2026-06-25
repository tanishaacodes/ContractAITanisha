"""
Management command to seed the dispute risk graph with 60 nodes and edges.
Based on the 8-layer Bayesian network architecture from the specification.
"""

from django.core.management.base import BaseCommand
from dispute_predictor.models import DisputeRiskNode, DisputeRiskEdge


class Command(BaseCommand):
    help = 'Seeds the dispute risk graph with 60 nodes and their relationships'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding dispute risk graph...')

        # Clear existing data
        DisputeRiskEdge.objects.all().delete()
        DisputeRiskNode.objects.all().delete()

        # Layer 1: Geopolitical Risks
        geo_nodes = self._create_nodes('geopolitical', 1, [
            ('war_risk', 'War Risk', 0.05),
            ('sanctions_risk', 'Sanctions Risk', 0.08),
            ('political_instability', 'Political Instability', 0.12),
            ('trade_restriction_risk', 'Trade Restriction Risk', 0.10),
            ('tariff_risk', 'Tariff Risk', 0.15),
            ('energy_security_risk', 'Energy Security Risk', 0.09),
            ('border_disruption', 'Border Disruption', 0.07),
            ('military_conflict_escalation', 'Military Conflict Escalation', 0.04),
        ])

        # Layer 2: Macroeconomic Risks
        macro_nodes = self._create_nodes('macroeconomic', 2, [
            ('inflation_risk', 'Inflation Risk', 0.35),
            ('interest_rate_shock', 'Interest Rate Shock', 0.20),
            ('currency_volatility', 'Currency Volatility', 0.22),
            ('commodity_price_volatility', 'Commodity Price Volatility', 0.25),
            ('energy_price_shock', 'Energy Price Shock', 0.18),
            ('global_demand_shock', 'Global Demand Shock', 0.16),
            ('logistics_cost_increase', 'Logistics Cost Increase', 0.28),
            ('credit_market_tightening', 'Credit Market Tightening', 0.19),
        ])

        # Layer 3: Market / Industry Risks
        market_nodes = self._create_nodes('market', 3, [
            ('competition_increase', 'Competition Increase', 0.30),
            ('demand_decline', 'Demand Decline', 0.22),
            ('market_price_pressure', 'Market Price Pressure', 0.26),
            ('technology_disruption', 'Technology Disruption', 0.18),
            ('regulatory_policy_change', 'Regulatory Policy Change', 0.15),
            ('esg_regulation', 'ESG Regulation', 0.14),
            ('environmental_regulation', 'Environmental Regulation', 0.13),
        ])

        # Layer 4: Supply Chain Risks
        supply_nodes = self._create_nodes('supply_chain', 4, [
            ('supplier_bankruptcy', 'Supplier Bankruptcy', 0.12),
            ('supplier_financial_stress', 'Supplier Financial Stress', 0.18),
            ('supplier_delay', 'Supplier Delay', 0.28),
            ('supplier_quality_failure', 'Supplier Quality Failure', 0.16),
            ('transport_disruption', 'Transport Disruption', 0.24),
            ('port_congestion', 'Port Congestion', 0.20),
            ('inventory_shortage', 'Inventory Shortage', 0.22),
            ('manufacturing_failure', 'Manufacturing Failure', 0.14),
        ])

        # Layer 5: Financial Risks
        financial_nodes = self._create_nodes('financial', 5, [
            ('counterparty_credit_risk', 'Counterparty Credit Risk', 0.18),
            ('payment_default_risk', 'Payment Default Risk', 0.20),
            ('cash_flow_stress', 'Cash Flow Stress', 0.24),
            ('financing_cost_increase', 'Financing Cost Increase', 0.26),
            ('working_capital_stress', 'Working Capital Stress', 0.22),
            ('contract_cost_overrun', 'Contract Cost Overrun', 0.30),
        ])

        # Layer 6: Operational Risks
        operational_nodes = self._create_nodes('operational', 6, [
            ('delivery_failure', 'Delivery Failure', 0.25),
            ('sla_violation', 'SLA Violation', 0.20),
            ('service_failure', 'Service Failure', 0.18),
            ('project_delay', 'Project Delay', 0.32),
            ('scope_change_risk', 'Scope Change Risk', 0.28),
            ('cost_escalation', 'Cost Escalation', 0.35),
        ])

        # Layer 7: Contract Risks
        contract_nodes = self._create_nodes('contract', 7, [
            ('contract_ambiguity', 'Contract Ambiguity', 0.40),
            ('clause_conflict', 'Clause Conflict', 0.35),
            ('liability_exposure', 'Liability Exposure', 0.30),
            ('termination_risk', 'Termination Risk', 0.25),
            ('renegotiation_risk', 'Renegotiation Risk', 0.28),
            ('contract_performance_risk', 'Contract Performance Risk', 0.45),
            ('contract_risk', 'Contract Risk', 0.50),
        ])

        # Layer 8: Legal Outcome Risks
        legal_nodes = self._create_nodes('legal_outcome', 8, [
            ('dispute_trigger', 'Dispute Trigger', 0.35),
            ('dispute_escalation', 'Dispute Escalation', 0.30),
            ('arbitration_initiation', 'Arbitration Initiation', 0.25),
            ('litigation_initiation', 'Litigation Initiation', 0.22),
            ('settlement_probability', 'Settlement Probability', 0.40),
            ('arbitration_win_probability', 'Arbitration Win Probability', 0.45),
            ('arbitration_loss_probability', 'Arbitration Loss Probability', 0.35),
            ('legal_cost_exposure', 'Legal Cost Exposure', 0.50),
            ('contract_termination', 'Contract Termination', 0.20),
            ('dispute_probability', 'Dispute Probability', 0.42),
        ])

        self.stdout.write(f'Created {DisputeRiskNode.objects.count()} risk nodes')

        # Create edges (relationships between nodes)
        edges_created = 0

        # Geopolitical → Macroeconomic
        edges_created += self._create_edges([
            (geo_nodes['war_risk'], macro_nodes['energy_price_shock'], 0.75),
            (geo_nodes['war_risk'], macro_nodes['commodity_price_volatility'], 0.70),
            (geo_nodes['sanctions_risk'], macro_nodes['currency_volatility'], 0.65),
            (geo_nodes['political_instability'], macro_nodes['currency_volatility'], 0.60),
            (geo_nodes['trade_restriction_risk'], macro_nodes['logistics_cost_increase'], 0.70),
            (geo_nodes['tariff_risk'], macro_nodes['logistics_cost_increase'], 0.65),
            (geo_nodes['energy_security_risk'], macro_nodes['energy_price_shock'], 0.80),
        ])

        # Macroeconomic → Market/Supply Chain
        edges_created += self._create_edges([
            (macro_nodes['inflation_risk'], market_nodes['market_price_pressure'], 0.75),
            (macro_nodes['interest_rate_shock'], financial_nodes['financing_cost_increase'], 0.80),
            (macro_nodes['commodity_price_volatility'], financial_nodes['contract_cost_overrun'], 0.70),
            (macro_nodes['energy_price_shock'], supply_nodes['manufacturing_failure'], 0.65),
            (macro_nodes['global_demand_shock'], market_nodes['demand_decline'], 0.75),
            (macro_nodes['logistics_cost_increase'], supply_nodes['transport_disruption'], 0.70),
            (macro_nodes['credit_market_tightening'], financial_nodes['counterparty_credit_risk'], 0.65),
        ])

        # Market → Supply Chain/Financial
        edges_created += self._create_edges([
            (market_nodes['competition_increase'], market_nodes['market_price_pressure'], 0.60),
            (market_nodes['demand_decline'], supply_nodes['supplier_financial_stress'], 0.70),
            (market_nodes['market_price_pressure'], financial_nodes['cash_flow_stress'], 0.65),
            (market_nodes['technology_disruption'], supply_nodes['supplier_bankruptcy'], 0.55),
            (market_nodes['regulatory_policy_change'], contract_nodes['renegotiation_risk'], 0.60),
        ])

        # Supply Chain → Operational
        edges_created += self._create_edges([
            (supply_nodes['supplier_delay'], operational_nodes['delivery_failure'], 0.75),
            (supply_nodes['supplier_bankruptcy'], operational_nodes['delivery_failure'], 0.85),
            (supply_nodes['supplier_quality_failure'], operational_nodes['sla_violation'], 0.65),
            (supply_nodes['transport_disruption'], operational_nodes['delivery_failure'], 0.70),
            (supply_nodes['port_congestion'], operational_nodes['project_delay'], 0.60),
            (supply_nodes['inventory_shortage'], operational_nodes['delivery_failure'], 0.68),
            (supply_nodes['manufacturing_failure'], operational_nodes['delivery_failure'], 0.80),
            (supply_nodes['supplier_financial_stress'], supply_nodes['supplier_delay'], 0.70),
        ])

        # Financial → Operational/Contract
        edges_created += self._create_edges([
            (financial_nodes['counterparty_credit_risk'], financial_nodes['payment_default_risk'], 0.70),
            (financial_nodes['payment_default_risk'], contract_nodes['termination_risk'], 0.75),
            (financial_nodes['cash_flow_stress'], operational_nodes['project_delay'], 0.65),
            (financial_nodes['financing_cost_increase'], financial_nodes['contract_cost_overrun'], 0.60),
            (financial_nodes['working_capital_stress'], financial_nodes['payment_default_risk'], 0.68),
            (financial_nodes['contract_cost_overrun'], operational_nodes['cost_escalation'], 0.75),
        ])

        # Operational → Contract
        edges_created += self._create_edges([
            (operational_nodes['delivery_failure'], contract_nodes['contract_performance_risk'], 0.80),
            (operational_nodes['sla_violation'], contract_nodes['contract_performance_risk'], 0.75),
            (operational_nodes['service_failure'], contract_nodes['contract_performance_risk'], 0.70),
            (operational_nodes['project_delay'], contract_nodes['contract_performance_risk'], 0.72),
            (operational_nodes['scope_change_risk'], contract_nodes['renegotiation_risk'], 0.65),
            (operational_nodes['cost_escalation'], contract_nodes['contract_performance_risk'], 0.78),
        ])

        # Contract → Legal Outcomes
        edges_created += self._create_edges([
            (contract_nodes['contract_ambiguity'], contract_nodes['clause_conflict'], 0.70),
            (contract_nodes['clause_conflict'], legal_nodes['dispute_trigger'], 0.75),
            (contract_nodes['liability_exposure'], legal_nodes['legal_cost_exposure'], 0.80),
            (contract_nodes['termination_risk'], legal_nodes['dispute_trigger'], 0.70),
            (contract_nodes['renegotiation_risk'], legal_nodes['dispute_escalation'], 0.60),
            (contract_nodes['contract_performance_risk'], contract_nodes['contract_risk'], 0.85),
            (contract_nodes['contract_ambiguity'], contract_nodes['contract_risk'], 0.75),
            (contract_nodes['contract_risk'], legal_nodes['dispute_trigger'], 0.80),
        ])

        # Legal Outcomes → Final Probabilities
        edges_created += self._create_edges([
            (legal_nodes['dispute_trigger'], legal_nodes['dispute_escalation'], 0.70),
            (legal_nodes['dispute_escalation'], legal_nodes['arbitration_initiation'], 0.45),
            (legal_nodes['dispute_escalation'], legal_nodes['litigation_initiation'], 0.35),
            (legal_nodes['dispute_escalation'], legal_nodes['settlement_probability'], 0.50),
            (legal_nodes['arbitration_initiation'], legal_nodes['arbitration_win_probability'], 0.50),
            (legal_nodes['arbitration_initiation'], legal_nodes['arbitration_loss_probability'], 0.50),
            (legal_nodes['arbitration_loss_probability'], legal_nodes['legal_cost_exposure'], 0.85),
            (legal_nodes['dispute_escalation'], legal_nodes['contract_termination'], 0.40),
            (legal_nodes['dispute_trigger'], legal_nodes['dispute_probability'], 0.90),
            (contract_nodes['contract_risk'], legal_nodes['dispute_probability'], 0.85),
            (financial_nodes['payment_default_risk'], legal_nodes['dispute_probability'], 0.70),
        ])

        self.stdout.write(self.style.SUCCESS(f'Successfully created {edges_created} edges'))
        self.stdout.write(self.style.SUCCESS(f'Total nodes: {DisputeRiskNode.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total edges: {DisputeRiskEdge.objects.count()}'))

    def _create_nodes(self, cluster, layer, nodes_data):
        """Create nodes for a specific layer and return dict mapping node_id to node_id."""
        nodes_dict = {}
        for node_id, label, base_prob in nodes_data:
            DisputeRiskNode.objects.create(
                node_id=node_id,
                label=label,
                cluster=cluster,
                layer=layer,
                base_probability=base_prob
            )
            nodes_dict[node_id] = node_id
        return nodes_dict

    def _create_edges(self, edges_data):
        """Create edges from list of (source_node_id, target_node_id, probability) tuples."""
        count = 0
        for source_id, target_id, prob in edges_data:
            DisputeRiskEdge.objects.create(
                source_node_id=source_id,
                target_node_id=target_id,
                conditional_probability=prob
            )
            count += 1
        return count
