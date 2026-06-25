"""
War Supply Chain Disruption Engine
Models impact of war/conflict on supply chains, shipping routes, and project dependencies
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SupplyNode:
    """Supply chain node (supplier, port, route, facility)"""
    node_id: str
    node_type: str  # supplier, port, warehouse, factory, route
    location: Dict  # {country, region, coordinates}
    capacity: float
    criticality: float  # 0-1
    alternatives: List[str]
    lead_time_days: int


@dataclass
class WarEvent:
    """War/conflict event affecting supply chains"""
    event_id: str
    event_type: str  # war, blockade, sanctions, strike, occupation
    affected_region: Dict
    severity: float  # 0-1
    start_date: datetime
    expected_duration_days: int
    affected_nodes: List[str]


class WarSupplyChainEngine:
    """Engine for analyzing war impact on supply chains"""

    def __init__(self):
        self.supply_graph = nx.DiGraph()
        self.war_events = []
        self._initialize_global_nodes()

    def _initialize_global_nodes(self):
        """Initialize major global supply chain nodes"""

        # Major ports
        major_ports = [
            {"id": "port_shanghai", "type": "port", "country": "China", "region": "East Asia", "capacity": 1.0},
            {"id": "port_singapore", "type": "port", "country": "Singapore", "region": "Southeast Asia", "capacity": 0.95},
            {"id": "port_rotterdam", "type": "port", "country": "Netherlands", "region": "Europe", "capacity": 0.90},
            {"id": "port_los_angeles", "type": "port", "country": "USA", "region": "North America", "capacity": 0.85},
            {"id": "port_dubai", "type": "port", "country": "UAE", "region": "Middle East", "capacity": 0.80},
            {"id": "port_odessa", "type": "port", "country": "Ukraine", "region": "Black Sea", "capacity": 0.30},  # War-affected
            {"id": "port_mariupol", "type": "port", "country": "Ukraine", "region": "Black Sea", "capacity": 0.0},  # Occupied
        ]

        # Critical shipping routes
        shipping_routes = [
            {"id": "suez_canal", "type": "route", "region": "Middle East", "criticality": 0.95, "alternatives": ["cape_good_hope"]},
            {"id": "panama_canal", "type": "route", "region": "Central America", "criticality": 0.90, "alternatives": ["strait_magellan"]},
            {"id": "strait_hormuz", "type": "route", "region": "Persian Gulf", "criticality": 0.85, "alternatives": ["overland_pipeline"]},
            {"id": "strait_malacca", "type": "route", "region": "Southeast Asia", "criticality": 0.80, "alternatives": ["sunda_strait"]},
            {"id": "black_sea_routes", "type": "route", "region": "Black Sea", "criticality": 0.70, "alternatives": ["baltic_routes"]},
            {"id": "red_sea_routes", "type": "route", "region": "Red Sea", "criticality": 0.75, "alternatives": ["suez_canal"]},
        ]

        # Add nodes to graph
        for port in major_ports:
            self.supply_graph.add_node(
                port["id"],
                node_type=port["type"],
                country=port.get("country", ""),
                region=port.get("region", ""),
                capacity=port.get("capacity", 1.0),
                criticality=port.get("capacity", 0.5)
            )

        for route in shipping_routes:
            self.supply_graph.add_node(
                route["id"],
                node_type=route["type"],
                region=route.get("region", ""),
                criticality=route.get("criticality", 0.5),
                alternatives=route.get("alternatives", [])
            )

        # Add supply chain edges (routes between ports)
        self._add_shipping_edges()

    def _add_shipping_edges(self):
        """Add edges representing shipping routes"""
        # Europe-Asia routes via Suez
        self.supply_graph.add_edge("port_rotterdam", "suez_canal", route_name="Europe-Suez", distance_km=6500)
        self.supply_graph.add_edge("suez_canal", "port_singapore", route_name="Suez-Asia", distance_km=8000)

        # Americas routes via Panama
        self.supply_graph.add_edge("port_los_angeles", "panama_canal", route_name="US-Panama", distance_km=4500)

        # Middle East oil routes
        self.supply_graph.add_edge("strait_hormuz", "suez_canal", route_name="Gulf-Suez", distance_km=3000)
        self.supply_graph.add_edge("port_dubai", "strait_hormuz", route_name="Dubai-Hormuz", distance_km=500)

        # Black Sea routes (Ukraine grain)
        self.supply_graph.add_edge("port_odessa", "black_sea_routes", route_name="Ukraine-BlackSea", distance_km=200)

        # Red Sea routes
        self.supply_graph.add_edge("red_sea_routes", "suez_canal", route_name="RedSea-Suez", distance_km=1500)

    def analyze_war_impact(
        self,
        war_event: Dict,
        contract_dependencies: List[Dict]
    ) -> Dict:
        """
        Analyze impact of war event on contract supply chains

        Args:
            war_event: Dict with type, location, severity, affected_areas
            contract_dependencies: List of contract dependencies (suppliers, routes, materials)

        Returns:
            Comprehensive impact analysis
        """
        event_type = war_event.get("type", "war")
        affected_region = war_event.get("region", "")
        severity = war_event.get("severity", 0.7)

        # Identify affected nodes
        affected_nodes = self._identify_affected_nodes(affected_region, severity)

        # Calculate disruption probability for each dependency
        dependency_impacts = []
        for dep in contract_dependencies:
            impact = self._calculate_dependency_impact(dep, affected_nodes, severity)
            dependency_impacts.append(impact)

        # Find alternative routes/suppliers
        alternatives = self._find_alternatives(dependency_impacts)

        # Calculate overall supply chain risk
        overall_risk = self._calculate_overall_risk(dependency_impacts)

        # Estimate delays and cost impacts
        delay_analysis = self._estimate_delays(dependency_impacts, alternatives)

        return {
            "war_event": war_event,
            "overall_risk_score": overall_risk,
            "affected_dependencies": len([d for d in dependency_impacts if d["disruption_probability"] > 0.3]),
            "total_dependencies": len(dependency_impacts),
            "dependency_impacts": dependency_impacts,
            "alternative_solutions": alternatives,
            "delay_analysis": delay_analysis,
            "cost_impact": self._estimate_cost_impact(delay_analysis, contract_dependencies),
            "mitigation_recommendations": self._generate_mitigations(dependency_impacts, alternatives)
        }

    def simulate_route_closure(
        self,
        route_id: str,
        closure_duration_days: int
    ) -> Dict:
        """
        Simulate closure of critical shipping route (e.g., Suez Canal)

        Args:
            route_id: ID of route to close
            closure_duration_days: Duration of closure

        Returns:
            Impact analysis with alternative routes and delays
        """
        if route_id not in self.supply_graph.nodes:
            return {"error": f"Route {route_id} not found"}

        route_node = self.supply_graph.nodes[route_id]
        alternatives = route_node.get("alternatives", [])

        # Find all paths using this route
        affected_paths = []
        for source in self.supply_graph.nodes:
            for target in self.supply_graph.nodes:
                if source != target:
                    try:
                        paths = list(nx.all_simple_paths(self.supply_graph, source, target, cutoff=10))
                        for path in paths:
                            if route_id in path:
                                affected_paths.append({
                                    "source": source,
                                    "target": target,
                                    "path": path,
                                    "alternative_available": len(alternatives) > 0
                                })
                    except nx.NetworkXNoPath:
                        continue

        # Calculate delays for alternative routes
        alternative_delays = {}
        for alt_route in alternatives:
            if alt_route in self.supply_graph.nodes:
                # Alternative routes typically add 7-14 days
                alternative_delays[alt_route] = {
                    "additional_delay_days": 10,  # Simplified
                    "additional_cost_pct": 25,
                    "capacity_pct": 80
                }

        return {
            "route_id": route_id,
            "route_name": route_node.get("route_name", route_id),
            "criticality": route_node.get("criticality", 0.5),
            "closure_duration_days": closure_duration_days,
            "affected_paths_count": len(affected_paths),
            "alternatives": alternative_delays,
            "estimated_global_impact": self._estimate_global_impact(route_id, affected_paths),
            "recommendations": self._get_route_closure_recommendations(route_id, alternatives)
        }

    def model_sanctions_impact(
        self,
        sanctioned_country: str,
        sanction_scope: List[str],  # ["energy", "finance", "shipping"]
        contract_exposure: Dict
    ) -> Dict:
        """
        Model impact of sanctions on contract supply chains

        Args:
            sanctioned_country: Country under sanctions
            sanction_scope: Sectors affected
            contract_exposure: Contract's exposure to sanctioned country

        Returns:
            Sanctions impact analysis
        """
        # Identify suppliers/routes in sanctioned country
        affected_nodes = [
            node_id for node_id, attrs in self.supply_graph.nodes(data=True)
            if attrs.get("country") == sanctioned_country
        ]

        # Calculate disruption by sector
        sector_impacts = {}
        for sector in sanction_scope:
            sector_impacts[sector] = {
                "disruption_probability": 0.90,  # Sanctions are highly disruptive
                "compliance_risk": 0.95,
                "alternative_cost_increase": 30,  # % increase
                "transition_time_days": 90
            }

        # Estimate total contract impact
        total_exposure = contract_exposure.get("total_value_pct", 0)
        affected_value = total_exposure * 0.90  # Assume 90% of exposure is disrupted

        return {
            "sanctioned_country": sanctioned_country,
            "sanction_scope": sanction_scope,
            "affected_nodes": affected_nodes,
            "affected_nodes_count": len(affected_nodes),
            "sector_impacts": sector_impacts,
            "contract_exposure_pct": total_exposure,
            "affected_contract_value_pct": affected_value,
            "compliance_actions_required": self._get_compliance_actions(sanction_scope),
            "alternative_suppliers": self._find_alternative_suppliers(sanctioned_country, affected_nodes),
            "transition_plan": self._generate_transition_plan(affected_nodes, 90)
        }

    def analyze_port_blockade(
        self,
        port_id: str,
        blockade_type: str,  # "naval", "strike", "customs"
        duration_estimate_days: int
    ) -> Dict:
        """
        Analyze impact of port blockade/closure

        Args:
            port_id: Port identifier
            blockade_type: Type of blockade
            duration_estimate_days: Expected duration

        Returns:
            Port blockade impact analysis
        """
        if port_id not in self.supply_graph.nodes:
            return {"error": f"Port {port_id} not found"}

        port_attrs = self.supply_graph.nodes[port_id]

        # Calculate cargo diversions
        diverted_cargo_pct = min(90, duration_estimate_days * 2)  # More cargo diverts over time

        # Find alternative ports
        alt_ports = self._find_nearby_ports(port_id, max_distance_km=500)

        # Estimate congestion at alternative ports
        congestion_impact = self._estimate_port_congestion(alt_ports, diverted_cargo_pct)

        return {
            "port_id": port_id,
            "port_capacity": port_attrs.get("capacity", 0),
            "blockade_type": blockade_type,
            "duration_estimate_days": duration_estimate_days,
            "diverted_cargo_pct": diverted_cargo_pct,
            "alternative_ports": alt_ports,
            "congestion_impact": congestion_impact,
            "estimated_delay_days": self._calculate_port_delay(diverted_cargo_pct, congestion_impact),
            "cost_impact_pct": diverted_cargo_pct * 0.3,  # 30% cost increase per 100% diversion
            "mitigation_options": self._get_port_mitigation_options(alt_ports)
        }

    # ============================================
    # HELPER METHODS
    # ============================================

    def _identify_affected_nodes(self, region: str, severity: float) -> List[str]:
        """Identify supply chain nodes affected by war event"""
        affected = []
        for node_id, attrs in self.supply_graph.nodes(data=True):
            node_region = attrs.get("region", "")
            if region.lower() in node_region.lower():
                # Node is in affected region
                disruption_prob = severity
                if attrs.get("node_type") == "port":
                    disruption_prob *= 0.8  # Ports may have some resilience
                affected.append({"node_id": node_id, "disruption_probability": disruption_prob})
        return affected

    def _calculate_dependency_impact(
        self,
        dependency: Dict,
        affected_nodes: List[Dict],
        severity: float
    ) -> Dict:
        """Calculate impact on specific dependency"""
        dep_location = dependency.get("location", "")
        dep_type = dependency.get("type", "supplier")

        # Check if dependency is in affected area
        is_affected = any(
            dep_location.lower() in node["node_id"].lower()
            for node in affected_nodes
        )

        if is_affected:
            disruption_prob = severity
            has_alternative = len(dependency.get("alternatives", [])) > 0

            return {
                "dependency_name": dependency.get("name", "Unknown"),
                "type": dep_type,
                "location": dep_location,
                "disruption_probability": disruption_prob,
                "has_alternative": has_alternative,
                "criticality": dependency.get("criticality", 0.5),
                "estimated_delay_days": int(severity * 90),  # Up to 90 days delay
                "mitigation_available": has_alternative
            }
        else:
            return {
                "dependency_name": dependency.get("name", "Unknown"),
                "type": dep_type,
                "location": dep_location,
                "disruption_probability": 0.0,
                "has_alternative": False,
                "criticality": dependency.get("criticality", 0.5),
                "estimated_delay_days": 0,
                "mitigation_available": True
            }

    def _find_alternatives(self, dependency_impacts: List[Dict]) -> List[Dict]:
        """Find alternative suppliers/routes for disrupted dependencies"""
        alternatives = []

        for dep in dependency_impacts:
            if dep["disruption_probability"] > 0.3:
                # Dependency is significantly disrupted
                alternative = {
                    "original_dependency": dep["dependency_name"],
                    "alternatives_found": [],
                    "transition_time_days": 45,
                    "additional_cost_pct": 20
                }

                # In production, query supplier databases, trade networks
                # For now, generate generic alternatives
                if dep["type"] == "supplier":
                    alternative["alternatives_found"] = [
                        {"name": "Alternative Supplier A", "location": "Safe Region", "capacity": 0.8},
                        {"name": "Alternative Supplier B", "location": "Safe Region", "capacity": 0.6}
                    ]
                elif dep["type"] == "route":
                    alternative["alternatives_found"] = [
                        {"name": "Alternative Route", "additional_days": 10, "cost_increase_pct": 25}
                    ]

                alternatives.append(alternative)

        return alternatives

    def _calculate_overall_risk(self, dependency_impacts: List[Dict]) -> float:
        """Calculate overall supply chain risk score"""
        if not dependency_impacts:
            return 0.0

        # Weighted average by criticality
        total_weighted_risk = sum(
            dep["disruption_probability"] * dep["criticality"]
            for dep in dependency_impacts
        )
        total_weight = sum(dep["criticality"] for dep in dependency_impacts)

        return total_weighted_risk / total_weight if total_weight > 0 else 0.0

    def _estimate_delays(
        self,
        dependency_impacts: List[Dict],
        alternatives: List[Dict]
    ) -> Dict:
        """Estimate project delays from supply chain disruptions"""
        max_delay = max(
            (dep["estimated_delay_days"] for dep in dependency_impacts),
            default=0
        )

        # With alternatives, reduce delay
        if alternatives:
            avg_transition_time = sum(alt["transition_time_days"] for alt in alternatives) / len(alternatives)
            effective_delay = max(max_delay * 0.5, avg_transition_time)
        else:
            effective_delay = max_delay

        return {
            "worst_case_delay_days": max_delay,
            "expected_delay_days": int(effective_delay),
            "best_case_delay_days": int(effective_delay * 0.5),
            "confidence": "medium"
        }

    def _estimate_cost_impact(
        self,
        delay_analysis: Dict,
        contract_dependencies: List[Dict]
    ) -> Dict:
        """Estimate cost impact from delays and rerouting"""
        delay_days = delay_analysis.get("expected_delay_days", 0)

        # Cost factors
        daily_carrying_cost = 50000  # $ per day (simplified)
        rerouting_cost_increase = 0.25  # 25% increase

        delay_cost = delay_days * daily_carrying_cost
        rerouting_cost = sum(
            dep.get("value", 1000000) * rerouting_cost_increase
            for dep in contract_dependencies
        )

        total_cost_impact = delay_cost + rerouting_cost

        return {
            "delay_cost_usd": delay_cost,
            "rerouting_cost_usd": rerouting_cost,
            "total_cost_impact_usd": total_cost_impact,
            "cost_breakdown": {
                "carrying_costs": delay_cost,
                "alternative_sourcing": rerouting_cost,
                "expediting_fees": delay_cost * 0.1
            }
        }

    def _generate_mitigations(
        self,
        dependency_impacts: List[Dict],
        alternatives: List[Dict]
    ) -> List[str]:
        """Generate mitigation recommendations"""
        mitigations = []

        high_risk_deps = [d for d in dependency_impacts if d["disruption_probability"] > 0.5]

        if high_risk_deps:
            mitigations.append(f"Activate {len(alternatives)} alternative suppliers/routes immediately")
            mitigations.append("Increase inventory buffers for critical materials by 60 days")
            mitigations.append("Negotiate force majeure clause extensions with project owner")

        if any(d["type"] == "route" for d in high_risk_deps):
            mitigations.append("Secure alternative shipping routes via air freight if needed")
            mitigations.append("Consider pre-positioning materials in safe locations")

        mitigations.append("Monitor war situation daily for escalation indicators")
        mitigations.append("Maintain communication with all suppliers in affected regions")

        return mitigations

    def _estimate_global_impact(self, route_id: str, affected_paths: List[Dict]) -> Dict:
        """Estimate global economic impact of route closure"""
        # Simplified model
        return {
            "affected_trade_volume_usd": len(affected_paths) * 1_000_000_000,  # $1B per path
            "global_gdp_impact_pct": len(affected_paths) * 0.01,  # 0.01% per path
            "price_impact_pct": min(50, len(affected_paths) * 2)  # Up to 50% price increases
        }

    def _get_route_closure_recommendations(
        self,
        route_id: str,
        alternatives: List[str]
    ) -> List[str]:
        """Get recommendations for route closure"""
        recs = [
            f"Immediately reroute shipments to: {', '.join(alternatives) if alternatives else 'overland routes'}",
            "Expect 10-14 days additional transit time",
            "Budget for 20-30% cost increase",
            "Monitor route status for reopening"
        ]
        return recs

    def _get_compliance_actions(self, sanction_scope: List[str]) -> List[str]:
        """Get compliance actions required for sanctions"""
        actions = [
            "Screen all suppliers against OFAC/UN/EU sanctions lists",
            "Terminate contracts with sanctioned entities immediately",
            "Conduct enhanced due diligence on replacement suppliers",
            "Update compliance policies and training",
            "File required reports with regulatory authorities"
        ]
        return actions

    def _find_alternative_suppliers(
        self,
        sanctioned_country: str,
        affected_nodes: List[str]
    ) -> List[Dict]:
        """Find alternative suppliers outside sanctioned country"""
        # Simplified - in production, query supplier databases
        return [
            {"name": "Alternative Supplier A", "country": "Germany", "transition_time_days": 60},
            {"name": "Alternative Supplier B", "country": "South Korea", "transition_time_days": 75}
        ]

    def _generate_transition_plan(
        self,
        affected_nodes: List[str],
        days: int
    ) -> List[Dict]:
        """Generate transition plan away from affected nodes"""
        return [
            {"week": 1, "action": "Identify alternative suppliers", "status": "immediate"},
            {"week": 2, "action": "Negotiate new contracts", "status": "immediate"},
            {"week": 4, "action": "Qualify new suppliers", "status": "urgent"},
            {"week": 8, "action": "Begin production with new suppliers", "status": "planned"},
            {"week": 12, "action": "Phase out affected suppliers completely", "status": "planned"}
        ]

    def _find_nearby_ports(self, port_id: str, max_distance_km: int) -> List[Dict]:
        """Find nearby alternative ports"""
        # Simplified - in production, use geospatial queries
        port_map = {
            "port_odessa": [
                {"id": "port_constanta", "country": "Romania", "distance_km": 250},
                {"id": "port_istanbul", "country": "Turkey", "distance_km": 400}
            ]
        }
        return port_map.get(port_id, [])

    def _estimate_port_congestion(
        self,
        alt_ports: List[Dict],
        diverted_cargo_pct: float
    ) -> Dict:
        """Estimate congestion at alternative ports"""
        return {
            "congestion_increase_pct": diverted_cargo_pct * 0.5,  # 50% of diverted cargo causes congestion
            "wait_time_increase_days": int(diverted_cargo_pct / 10),  # 1 day per 10% diversion
            "capacity_utilization_pct": min(100, 70 + diverted_cargo_pct * 0.3)
        }

    def _calculate_port_delay(
        self,
        diverted_cargo_pct: float,
        congestion_impact: Dict
    ) -> int:
        """Calculate total port delay"""
        return congestion_impact.get("wait_time_increase_days", 0) + int(diverted_cargo_pct / 20)

    def _get_port_mitigation_options(self, alt_ports: List[Dict]) -> List[str]:
        """Get mitigation options for port disruptions"""
        return [
            f"Divert to {len(alt_ports)} alternative ports",
            "Use overland routes if available",
            "Consider air freight for critical cargo",
            "Negotiate priority berthing at alternative ports"
        ]


# Global instance
war_supply_chain_engine = WarSupplyChainEngine()


# Convenience functions
def analyze_war_supply_chain_impact(contract_data: Dict) -> Dict:
    """Analyze war impact on contract supply chain"""
    war_event = {
        "type": "war",
        "region": contract_data.get("project_location", {}).get("region", ""),
        "severity": 0.8
    }

    dependencies = contract_data.get("supply_chain_dependencies", [])

    return war_supply_chain_engine.analyze_war_impact(war_event, dependencies)
