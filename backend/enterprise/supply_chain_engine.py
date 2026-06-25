"""
Advanced Supply Chain Risk Engine
Multi-tier supplier analysis with cascading risk propagation
"""
import logging
from typing import Dict, List
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


class SupplyChainRiskEngine:
    """
    Advanced supply chain risk analysis with multi-tier modeling
    """

    @staticmethod
    def calculate_multi_tier_risk(contract_id: str) -> Dict:
        """
        Calculate comprehensive supply chain risk including sub-supplier dependencies

        Args:
            contract_id: Contract ID

        Returns:
            Dictionary with multi-tier risk metrics
        """
        from .models import ContractSupplier, SupplierDependency

        # Get direct suppliers (Tier 1)
        tier_1_suppliers = ContractSupplier.objects.filter(
            contract_id=contract_id
        ).select_related('supplier')

        if not tier_1_suppliers.exists():
            return {
                'total_risk_score': 0.0,
                'tier_1_risk': 0.0,
                'tier_2_risk': 0.0,
                'tier_3_risk': 0.0,
                'cascading_risk_multiplier': 1.0,
                'single_source_count': 0,
                'critical_dependencies': []
            }

        # Calculate Tier 1 risk
        tier_1_risk = 0.0
        tier_1_exposure = Decimal('0')
        single_source_count = 0

        tier_1_details = []

        for cs in tier_1_suppliers:
            supplier = cs.supplier
            exposure = float(cs.exposure_amount)

            tier_1_risk += supplier.risk_score * (exposure / 1_000_000)  # Weight by exposure
            tier_1_exposure += cs.exposure_amount

            if supplier.is_single_source:
                single_source_count += 1

            tier_1_details.append({
                'name': supplier.name,
                'risk_score': supplier.risk_score,
                'exposure': exposure,
                'is_single_source': supplier.is_single_source
            })

        # Normalize Tier 1 risk
        if float(tier_1_exposure) > 0:
            tier_1_risk = tier_1_risk / (float(tier_1_exposure) / 1_000_000)
        else:
            tier_1_risk = 0.5

        # Calculate Tier 2 and Tier 3 cascading risk
        tier_2_risk = 0.0
        tier_3_risk = 0.0
        critical_dependencies = []

        for cs in tier_1_suppliers:
            tier_1_supplier = cs.supplier

            # Get sub-suppliers (Tier 2)
            tier_2_dependencies = SupplierDependency.objects.filter(
                parent_supplier=tier_1_supplier
            ).select_related('child_supplier')

            for dep in tier_2_dependencies:
                tier_2_supplier = dep.child_supplier
                tier_2_risk += tier_2_supplier.risk_score * dep.criticality

                # Check if this is a critical dependency
                if dep.criticality >= 0.7:
                    critical_dependencies.append({
                        'tier_1': tier_1_supplier.name,
                        'tier_2': tier_2_supplier.name,
                        'criticality': dep.criticality,
                        'dependency_type': dep.dependency_type,
                        'lead_time_days': dep.lead_time_days
                    })

                # Get Tier 3 (sub-suppliers of sub-suppliers)
                tier_3_dependencies = SupplierDependency.objects.filter(
                    parent_supplier=tier_2_supplier
                ).select_related('child_supplier')

                for tier_3_dep in tier_3_dependencies:
                    tier_3_supplier = tier_3_dep.child_supplier
                    tier_3_risk += tier_3_supplier.risk_score * tier_3_dep.criticality * 0.5

        # Normalize Tier 2 and Tier 3 risks
        tier_2_count = SupplierDependency.objects.filter(
            parent_supplier__in=[cs.supplier for cs in tier_1_suppliers]
        ).count()

        if tier_2_count > 0:
            tier_2_risk = tier_2_risk / tier_2_count
        else:
            tier_2_risk = 0.0

        # Calculate cascading risk multiplier
        # Higher tier risks amplify overall risk
        cascading_multiplier = 1.0 + (tier_2_risk * 0.3) + (tier_3_risk * 0.15)

        # Calculate total risk score
        total_risk_score = (
            tier_1_risk * 0.60 +  # 60% weight on direct suppliers
            tier_2_risk * 0.30 +  # 30% weight on sub-suppliers
            tier_3_risk * 0.10    # 10% weight on tertiary suppliers
        ) * cascading_multiplier

        # Cap risk score
        total_risk_score = min(total_risk_score, 1.0)

        return {
            'total_risk_score': round(total_risk_score, 4),
            'tier_1_risk': round(tier_1_risk, 4),
            'tier_2_risk': round(tier_2_risk, 4),
            'tier_3_risk': round(tier_3_risk, 4),
            'cascading_risk_multiplier': round(cascading_multiplier, 4),
            'single_source_count': single_source_count,
            'critical_dependencies': critical_dependencies,
            'tier_1_suppliers': tier_1_details,
            'tier_breakdown': {
                'tier_1_count': tier_1_suppliers.count(),
                'tier_2_count': tier_2_count,
                'tier_3_count': SupplierDependency.objects.filter(
                    parent_supplier__parent_suppliers__isnull=False
                ).count()
            }
        }

    @staticmethod
    def calculate_concentration_risk(contract_id: str) -> Dict:
        """
        Calculate supplier concentration risk (Herfindahl-Hirschman Index)

        Args:
            contract_id: Contract ID

        Returns:
            Concentration risk metrics
        """
        from .models import ContractSupplier

        suppliers = ContractSupplier.objects.filter(contract_id=contract_id)

        if not suppliers.exists():
            return {
                'hhi': 0.0,
                'concentration_level': 'NONE',
                'dominant_supplier': None
            }

        # Calculate total exposure
        total_exposure = sum(float(s.exposure_amount) for s in suppliers)

        if total_exposure == 0:
            return {
                'hhi': 0.0,
                'concentration_level': 'NONE',
                'dominant_supplier': None
            }

        # Calculate HHI (sum of squared market shares)
        hhi = 0.0
        max_share = 0.0
        dominant_supplier = None

        for supplier_contract in suppliers:
            share = float(supplier_contract.exposure_amount) / total_exposure
            hhi += share ** 2

            if share > max_share:
                max_share = share
                dominant_supplier = {
                    'name': supplier_contract.supplier.name,
                    'share': round(share * 100, 2)
                }

        # Determine concentration level
        if hhi < 0.15:
            concentration_level = 'LOW'
        elif hhi < 0.25:
            concentration_level = 'MODERATE'
        else:
            concentration_level = 'HIGH'

        return {
            'hhi': round(hhi, 4),
            'concentration_level': concentration_level,
            'dominant_supplier': dominant_supplier,
            'diversification_score': round(1 - hhi, 4)
        }

    @staticmethod
    def identify_single_points_of_failure(contract_id: str) -> List[Dict]:
        """
        Identify critical single points of failure in supply chain

        Args:
            contract_id: Contract ID

        Returns:
            List of single points of failure
        """
        from .models import ContractSupplier, SupplierDependency

        single_points = []

        # Check Tier 1 single-source suppliers
        tier_1_suppliers = ContractSupplier.objects.filter(
            contract_id=contract_id,
            supplier__is_single_source=True
        ).select_related('supplier')

        for cs in tier_1_suppliers:
            single_points.append({
                'tier': 1,
                'supplier': cs.supplier.name,
                'reason': 'Single-source supplier',
                'impact': 'HIGH',
                'exposure': float(cs.exposure_amount),
                'mitigation': 'Identify backup suppliers'
            })

        # Check for critical Tier 2 dependencies
        for cs in ContractSupplier.objects.filter(contract_id=contract_id):
            critical_deps = SupplierDependency.objects.filter(
                parent_supplier=cs.supplier,
                criticality__gte=0.8,
                child_supplier__is_single_source=True
            ).select_related('child_supplier')

            for dep in critical_deps:
                single_points.append({
                    'tier': 2,
                    'supplier': dep.child_supplier.name,
                    'parent': cs.supplier.name,
                    'reason': 'Critical sub-supplier with no alternatives',
                    'impact': 'CRITICAL',
                    'criticality': dep.criticality,
                    'mitigation': 'Urgent: Establish backup supply chain'
                })

        return single_points
