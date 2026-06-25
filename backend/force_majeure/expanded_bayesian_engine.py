"""
Expanded Bayesian Network Engine (100+ Nodes)
Extended from 35 to 100+ nodes for more granular FM risk modeling
"""

import logging
from typing import Dict, List, Optional
from .bayesian_engine import FMBayesianEngine

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# EXPANDED 100+ NODE BAYESIAN NETWORK
# ═══════════════════════════════════════════════════════════════

# Layer 1: Root Events (35 nodes - expanded from 15)
EXPANDED_LAYER1_ROOT_EVENTS = [
    # Original 15
    'war', 'regional_conflict', 'cyber_warfare', 'terrorism', 'pandemic', 'epidemic',
    'earthquake', 'flood', 'hurricane', 'wildfire', 'volcanic_eruption',
    'political_coup', 'trade_sanctions', 'economic_collapse', 'energy_crisis',

    # 20 Additional root events
    'civil_war', 'military_invasion', 'border_conflict', 'naval_blockade',
    'drone_strikes', 'nuclear_incident', 'chemical_attack', 'biological_attack',
    'tsunami', 'tornado', 'drought', 'extreme_heat', 'extreme_cold', 'landslide',
    'government_expropriation', 'martial_law', 'currency_collapse', 'banking_crisis',
    'trade_war', 'supply_shortage', 'labor_unrest', 'social_unrest',
    'refugee_crisis', 'water_crisis', 'food_crisis'
]

# Layer 2: Intermediate Disruptions (30 nodes - expanded from 12)
EXPANDED_LAYER2_DISRUPTIONS = [
    # Original 12
    'sanctions_expansion', 'currency_volatility', 'commodity_price_shock',
    'energy_price_spike', 'labor_shortage', 'factory_shutdown',
    'transport_shutdown', 'port_closure', 'airspace_closure',
    'telecom_disruption', 'power_grid_failure', 'financial_market_crash',

    # 18 Additional disruptions
    'border_closure', 'customs_delays', 'export_restrictions', 'import_restrictions',
    'visa_restrictions', 'travel_ban', 'quarantine_measures', 'curfew',
    'internet_shutdown', 'banking_suspension', 'payment_freeze', 'asset_seizure',
    'license_revocation', 'permit_suspension', 'inspection_delays', 'certification_delays',
    'workforce_exodus', 'skill_shortage'
]

# Layer 3: Supply Chain Impacts (25 nodes - expanded from 8)
EXPANDED_LAYER3_SUPPLY_IMPACTS = [
    # Original 8
    'supplier_failure', 'inventory_shortage', 'logistics_delay',
    'shipping_route_disruption', 'manufacturing_delay', 'equipment_delivery_delay',
    'commodity_cost_escalation', 'insurance_premium_spike',

    # 17 Additional supply impacts
    'raw_material_shortage', 'component_unavailability', 'spare_parts_shortage',
    'packaging_shortage', 'container_shortage', 'truck_shortage', 'warehouse_closure',
    'quality_control_failure', 'production_stoppage', 'assembly_line_shutdown',
    'maintenance_delays', 'inspection_failures', 'customs_seizure',
    'transport_damage', 'storage_damage', 'expiry_losses', 'obsolescence'
]

# Layer 4: Contract Outcomes (15 nodes - expanded from 6)
EXPANDED_LAYER4_OUTCOMES = [
    # Original 6
    'project_delay', 'cost_overrun', 'contract_suspension',
    'insurance_claim', 'fm_invocation', 'contract_termination',

    # 9 Additional outcomes
    'penalty_application', 'liquidated_damages', 'performance_bond_call',
    'arbitration_filing', 'litigation', 'force_majeure_negotiation',
    'contract_variation', 'scope_reduction', 'early_termination'
]

# All expanded nodes
ALL_EXPANDED_NODES = (
    EXPANDED_LAYER1_ROOT_EVENTS +
    EXPANDED_LAYER2_DISRUPTIONS +
    EXPANDED_LAYER3_SUPPLY_IMPACTS +
    EXPANDED_LAYER4_OUTCOMES
)

TOTAL_NODES = len(ALL_EXPANDED_NODES)  # Should be 105 nodes


class ExpandedBayesianEngine(FMBayesianEngine):
    """Extended Bayesian engine with 100+ nodes for granular risk modeling"""

    def __init__(self):
        super().__init__()
        self._extend_network()

    def _extend_network(self):
        """Extend the network with additional nodes and dependencies"""

        # Add new root events
        new_root_events = [
            'civil_war', 'military_invasion', 'border_conflict', 'naval_blockade',
            'drone_strikes', 'nuclear_incident', 'chemical_attack', 'biological_attack',
            'tsunami', 'tornado', 'drought', 'extreme_heat', 'extreme_cold', 'landslide',
            'government_expropriation', 'martial_law', 'currency_collapse', 'banking_crisis',
            'trade_war', 'supply_shortage', 'labor_unrest', 'social_unrest',
            'refugee_crisis', 'water_crisis', 'food_crisis'
        ]

        # Add new disruptions
        new_disruptions = [
            'border_closure', 'customs_delays', 'export_restrictions', 'import_restrictions',
            'visa_restrictions', 'travel_ban', 'quarantine_measures', 'curfew',
            'internet_shutdown', 'banking_suspension', 'payment_freeze', 'asset_seizure',
            'license_revocation', 'permit_suspension', 'inspection_delays', 'certification_delays',
            'workforce_exodus', 'skill_shortage'
        ]

        # Add new supply impacts
        new_supply_impacts = [
            'raw_material_shortage', 'component_unavailability', 'spare_parts_shortage',
            'packaging_shortage', 'container_shortage', 'truck_shortage', 'warehouse_closure',
            'quality_control_failure', 'production_stoppage', 'assembly_line_shutdown',
            'maintenance_delays', 'inspection_failures', 'customs_seizure',
            'transport_damage', 'storage_damage', 'expiry_losses', 'obsolescence'
        ]

        # Add new outcomes
        new_outcomes = [
            'penalty_application', 'liquidated_damages', 'performance_bond_call',
            'arbitration_filing', 'litigation', 'force_majeure_negotiation',
            'contract_variation', 'scope_reduction', 'early_termination'
        ]

        # Extend CPT tables with new dependencies
        self._add_expanded_dependencies()

    def _add_expanded_dependencies(self):
        """Add dependencies for new nodes"""

        # New war-related dependencies
        self.cpt['civil_war'] = {}
        self.cpt['military_invasion'] = {}
        self.cpt['border_conflict'] = {}
        self.cpt['naval_blockade'] = {('war', True): 0.70}
        self.cpt['drone_strikes'] = {('war', True): 0.60, ('terrorism', True): 0.50}

        # Nuclear/chemical/biological
        self.cpt['nuclear_incident'] = {('war', True): 0.15}
        self.cpt['chemical_attack'] = {('war', True): 0.20, ('terrorism', True): 0.30}
        self.cpt['biological_attack'] = {('pandemic', True): 0.10, ('terrorism', True): 0.25}

        # Additional natural disasters
        self.cpt['tsunami'] = {('earthquake', True): 0.40}
        self.cpt['tornado'] = {('hurricane', True): 0.35}
        self.cpt['drought'] = {('extreme_heat', True): 0.60}
        self.cpt['landslide'] = {('flood', True): 0.30, ('earthquake', True): 0.25}

        # Additional government actions
        self.cpt['government_expropriation'] = {('political_coup', True): 0.50}
        self.cpt['martial_law'] = {('political_coup', True): 0.60, ('civil_war', True): 0.70}

        # Economic crises
        self.cpt['currency_collapse'] = {('economic_collapse', True): 0.75}
        self.cpt['banking_crisis'] = {('economic_collapse', True): 0.70}
        self.cpt['trade_war'] = {('trade_sanctions', True): 0.50}

        # Social/humanitarian
        self.cpt['labor_unrest'] = {('economic_collapse', True): 0.40}
        self.cpt['social_unrest'] = {('political_coup', True): 0.55, ('economic_collapse', True): 0.45}
        self.cpt['refugee_crisis'] = {('war', True): 0.60, ('civil_war', True): 0.70}
        self.cpt['water_crisis'] = {('drought', True): 0.65}
        self.cpt['food_crisis'] = {('drought', True): 0.55, ('supply_shortage', True): 0.50}

        # New disruptions caused by root events
        self.cpt['border_closure'] = {
            ('war', True): 0.75,
            ('pandemic', True): 0.80,
            ('civil_war', True): 0.70
        }
        self.cpt['customs_delays'] = {
            ('border_closure', True): 0.60,
            ('trade_war', True): 0.50
        }
        self.cpt['export_restrictions'] = {('trade_sanctions', True): 0.70, ('trade_war', True): 0.60}
        self.cpt['import_restrictions'] = {('trade_sanctions', True): 0.70, ('trade_war', True): 0.60}
        self.cpt['visa_restrictions'] = {('war', True): 0.50, ('pandemic', True): 0.60}
        self.cpt['travel_ban'] = {('war', True): 0.65, ('pandemic', True): 0.75}
        self.cpt['quarantine_measures'] = {('pandemic', True): 0.85, ('epidemic', True): 0.70}
        self.cpt['curfew'] = {('martial_law', True): 0.80, ('social_unrest', True): 0.60}

        self.cpt['internet_shutdown'] = {('political_coup', True): 0.50, ('cyber_warfare', True): 0.40}
        self.cpt['banking_suspension'] = {('banking_crisis', True): 0.60, ('economic_collapse', True): 0.50}
        self.cpt['payment_freeze'] = {('banking_crisis', True): 0.55, ('currency_collapse', True): 0.60}
        self.cpt['asset_seizure'] = {('government_expropriation', True): 0.75, ('trade_sanctions', True): 0.45}

        self.cpt['license_revocation'] = {('government_expropriation', True): 0.50}
        self.cpt['permit_suspension'] = {('political_coup', True): 0.40}
        self.cpt['inspection_delays'] = {('customs_delays', True): 0.55, ('border_closure', True): 0.50}
        self.cpt['certification_delays'] = {('border_closure', True): 0.45}

        self.cpt['workforce_exodus'] = {
            ('war', True): 0.60,
            ('refugee_crisis', True): 0.70,
            ('economic_collapse', True): 0.45
        }
        self.cpt['skill_shortage'] = {('workforce_exodus', True): 0.65, ('labor_shortage', True): 0.50}

        # New supply chain impacts
        self.cpt['raw_material_shortage'] = {
            ('supplier_failure', True): 0.70,
            ('border_closure', True): 0.55,
            ('export_restrictions', True): 0.60
        }
        self.cpt['component_unavailability'] = {
            ('supplier_failure', True): 0.65,
            ('manufacturing_delay', True): 0.50
        }
        self.cpt['spare_parts_shortage'] = {('supplier_failure', True): 0.60}
        self.cpt['packaging_shortage'] = {('supply_shortage', True): 0.50}
        self.cpt['container_shortage'] = {
            ('port_closure', True): 0.55,
            ('shipping_route_disruption', True): 0.50
        }
        self.cpt['truck_shortage'] = {('transport_shutdown', True): 0.60, ('labor_shortage', True): 0.45}
        self.cpt['warehouse_closure'] = {('power_grid_failure', True): 0.50, ('factory_shutdown', True): 0.45}

        self.cpt['quality_control_failure'] = {('labor_shortage', True): 0.40, ('skill_shortage', True): 0.45}
        self.cpt['production_stoppage'] = {
            ('factory_shutdown', True): 0.80,
            ('power_grid_failure', True): 0.70,
            ('raw_material_shortage', True): 0.60
        }
        self.cpt['assembly_line_shutdown'] = {
            ('production_stoppage', True): 0.75,
            ('component_unavailability', True): 0.65
        }
        self.cpt['maintenance_delays'] = {('spare_parts_shortage', True): 0.60, ('skill_shortage', True): 0.45}
        self.cpt['inspection_failures'] = {('quality_control_failure', True): 0.55}
        self.cpt['customs_seizure'] = {('customs_delays', True): 0.20}
        self.cpt['transport_damage'] = {('logistics_delay', True): 0.15}
        self.cpt['storage_damage'] = {('warehouse_closure', True): 0.25}
        self.cpt['expiry_losses'] = {('logistics_delay', True): 0.20, ('storage_damage', True): 0.30}
        self.cpt['obsolescence'] = {('project_delay', True): 0.25}

        # New contract outcomes
        self.cpt['penalty_application'] = {
            ('project_delay', True): 0.65,
            ('cost_overrun', True): 0.45
        }
        self.cpt['liquidated_damages'] = {
            ('project_delay', True): 0.70,
            ('penalty_application', True): 0.80
        }
        self.cpt['performance_bond_call'] = {
            ('contract_suspension', True): 0.50,
            ('liquidated_damages', True): 0.60
        }
        self.cpt['arbitration_filing'] = {
            ('fm_invocation', True): 0.35,
            ('liquidated_damages', True): 0.45
        }
        self.cpt['litigation'] = {
            ('arbitration_filing', True): 0.40,
            ('contract_termination', True): 0.50
        }
        self.cpt['force_majeure_negotiation'] = {
            ('fm_invocation', True): 0.75
        }
        self.cpt['contract_variation'] = {
            ('cost_overrun', True): 0.40,
            ('project_delay', True): 0.35
        }
        self.cpt['scope_reduction'] = {
            ('contract_variation', True): 0.45,
            ('cost_overrun', True): 0.50
        }
        self.cpt['early_termination'] = {
            ('contract_termination', True): 0.60,
            ('fm_invocation', True): 0.30
        }

    def get_node_count(self) -> Dict:
        """Get count of nodes by layer"""
        return {
            'layer1_root_events': len(EXPANDED_LAYER1_ROOT_EVENTS),
            'layer2_disruptions': len(EXPANDED_LAYER2_DISRUPTIONS),
            'layer3_supply_impacts': len(EXPANDED_LAYER3_SUPPLY_IMPACTS),
            'layer4_outcomes': len(EXPANDED_LAYER4_OUTCOMES),
            'total_nodes': TOTAL_NODES
        }


# Global instance
expanded_bayesian_engine = ExpandedBayesianEngine()


# Convenience function
def get_expanded_engine():
    """Get the expanded 100+ node Bayesian engine"""
    return expanded_bayesian_engine
