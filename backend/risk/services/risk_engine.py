"""
Cross-Contract Risk Engine
Main orchestrator for risk analysis using Neo4j, Qdrant, and LLM services
"""
from .neo4j import get_neo4j_service
from .qdrant_service import get_qdrant_service
from .llm_risk_scorer import get_llm_risk_scorer
from ..models import (
    Party, PartyPartition, ContractRisk, ClauseRisk,
    VendorExposure, CrossContractCorrelation, RiskNode
)
from core.models import Contract, Clause
from django.db import transaction
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Main risk analysis engine that coordinates Neo4j, Qdrant, and LLM services
    to provide cross-contract risk intelligence.
    """

    def __init__(self):
        """Initialize risk engine with all services"""
        self.neo4j = get_neo4j_service()
        self.qdrant = get_qdrant_service()
        self.llm_scorer = get_llm_risk_scorer()
        logger.info("Risk Engine initialized")

    def analyze_contract(self, contract_id):
        """
        Full risk analysis of a contract: scores clauses, syncs to Neo4j/Qdrant.

        Args:
            contract_id: Contract UUID

        Returns:
            Risk analysis results
        """
        try:
            contract = Contract.objects.get(id=contract_id)
            clauses = Clause.objects.filter(contract=contract)

            logger.info(f"Analyzing contract {contract_id}: {len(clauses)} clauses")

            clause_risks = []

            with transaction.atomic():
                for clause in clauses:
                    # Score clause risk using LLM
                    risk_data = self.llm_scorer.score_clause_risk(
                        clause.extracted_text or clause.text_spans or "",
                        clause.clause_type
                    )

                    # Store in MySQL
                    clause_risk, created = ClauseRisk.objects.update_or_create(
                        clause=clause,
                        defaults={
                            "local_risk_score": risk_data["risk_score"]
                        }
                    )

                    # Store embedding in Qdrant
                    clause_text = clause.extracted_text or clause.text_spans or ""
                    if clause_text:
                        clause_hash = self.qdrant.store_clause_embedding(
                            clause.id,
                            clause_text,
                            metadata={
                                "contract_id": str(contract.id),
                                "category": clause.clause_type or "Unknown",
                                "risk_score": risk_data["risk_score"]
                            }
                        )

                        # Update Qdrant point ID
                        clause_risk.qdrant_point_id = clause_hash
                        clause_risk.embedding_synced_at = datetime.now()
                        clause_risk.save()

                        # Sync to Neo4j
                        self._sync_clause_to_neo4j(clause, clause_hash, risk_data["risk_score"])

                    clause_risks.append(risk_data)

                # Calculate overall contract risk
                overall_analysis = self.llm_scorer.analyze_contract_risk(clause_risks)

                # Extract or get party (vendor/customer)
                party = self._get_or_create_party(contract)

                # Store contract risk
                contract_risk, created = ContractRisk.objects.update_or_create(
                    contract=contract,
                    defaults={
                        "party": party,
                        "overall_risk_score": overall_analysis["overall_risk_score"],
                        "region": contract.jurisdiction,  # Using jurisdiction as region
                        "business_unit": "Default",  # Could be extracted from contract metadata
                        "last_synced_at": datetime.now()
                    }
                )

                # Sync contract to Neo4j
                self._sync_contract_to_neo4j(contract, party, overall_analysis["overall_risk_score"])

            logger.info(f"Contract analysis complete: {contract_id}")

            return {
                "contract_id": str(contract.id),
                "overall_risk": overall_analysis,
                "clause_count": len(clauses),
                "clauses_analyzed": len(clause_risks)
            }

        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            raise

    def _get_or_create_party(self, contract):
        """Extract or create party from contract"""
        # Try to get vendor/customer from contract fields
        party_name = contract.party_b or contract.party_name or "Unknown Party"

        party, created = Party.objects.get_or_create(
            name=party_name,
            defaults={
                "party_type": "VENDOR",  # Default assumption
                "country": contract.jurisdiction
            }
        )

        if created:
            # Sync to Neo4j
            self.neo4j.upsert_party(party.id, party.name, party.party_type, party.country)

        return party

    def _sync_contract_to_neo4j(self, contract, party, risk_score):
        """Sync contract to Neo4j graph"""
        try:
            # Upsert contract node
            self.neo4j.upsert_contract(
                contract.id,
                float(contract.contract_value.replace("$", "").replace(",", "")) if contract.contract_value else 0.0,
                contract.jurisdiction,
                "Default",  # Business unit
                risk_score
            )

            # Link to party via partition
            year = contract.created_at.year if contract.created_at else 2025
            partition_key = f"{party.name}_{year}"

            self.neo4j.upsert_party_partition(partition_key, party.id, year, contract.jurisdiction)
            self.neo4j.link_party_contract(party.id, partition_key, contract.id, year)

            logger.info(f"Synced contract to Neo4j: {contract.id}")

        except Exception as e:
            logger.error(f"Error syncing contract to Neo4j: {e}")

    def _sync_clause_to_neo4j(self, clause, clause_hash, risk_score):
        """Sync clause to Neo4j graph"""
        try:
            # Upsert clause node
            self.neo4j.upsert_clause(
                clause_hash,
                clause.clause_type or "Unknown",
                risk_score
            )

            # Link contract to clause
            self.neo4j.link_contract_clause(
                clause.contract.id,
                clause_hash,
                risk_score,
                negotiated=False  # Could be extracted from clause metadata
            )

            logger.info(f"Synced clause to Neo4j: {clause.clause_name}")

        except Exception as e:
            logger.error(f"Error syncing clause to Neo4j: {e}")

    def calculate_vendor_exposure(self, vendor_name, region=None):
        """
        Calculate total risk exposure for a vendor across all contracts.

        Args:
            vendor_name: Vendor name
            region: Optional region filter

        Returns:
            Exposure analysis
        """
        try:
            # Query Neo4j for vendor exposure
            exposure_score = self.neo4j.get_vendor_exposure(vendor_name, region)

            # Get MySQL data for context
            party = Party.objects.filter(name=vendor_name).first()

            if party:
                contracts = ContractRisk.objects.filter(party=party)
                if region:
                    contracts = contracts.filter(region=region)

                contract_count = contracts.count()
                avg_risk = contracts.aggregate(models.Avg('overall_risk_score'))['overall_risk_score__avg'] or 0

                # Update or create vendor exposure record
                vendor_exposure, created = VendorExposure.objects.update_or_create(
                    party=party,
                    defaults={
                        "total_exposure": exposure_score,
                        "contract_count": contract_count,
                        "average_risk": avg_risk
                    }
                )

                return {
                    "vendor_name": vendor_name,
                    "total_exposure": exposure_score,
                    "contract_count": contract_count,
                    "average_risk": round(avg_risk, 2),
                    "region": region
                }
            else:
                return {
                    "vendor_name": vendor_name,
                    "total_exposure": 0.0,
                    "contract_count": 0,
                    "average_risk": 0.0,
                    "region": region
                }

        except Exception as e:
            logger.error(f"Error calculating vendor exposure: {e}")
            raise

    def detect_cross_contract_correlations(self, contract_id):
        """
        Detect correlations between contracts based on similar clauses.

        Args:
            contract_id: Contract UUID

        Returns:
            List of correlated contracts
        """
        try:
            contract = Contract.objects.get(id=contract_id)
            clauses = Clause.objects.filter(contract=contract)

            correlations = []

            for clause in clauses:
                clause_text = clause.extracted_text or clause.text_spans or ""
                if not clause_text:
                    continue

                # Find similar clauses in Qdrant
                similar_clauses = self.qdrant.find_similar_clauses(
                    clause_text,
                    limit=20,
                    score_threshold=0.8  # High similarity threshold
                )

                for similar in similar_clauses:
                    similar_contract_id = similar.get("contract_id")
                    if similar_contract_id and similar_contract_id != str(contract.id):
                        # Check if correlation already exists
                        existing = CrossContractCorrelation.objects.filter(
                            contract_a=contract,
                            contract_b_id=similar_contract_id
                        ).first()

                        if not existing:
                            # Create correlation
                            similar_contract = Contract.objects.get(id=similar_contract_id)

                            correlation = CrossContractCorrelation.objects.create(
                                contract_a=contract,
                                contract_b=similar_contract,
                                correlation_strength=similar["similarity_score"],
                                correlation_reason=f"Similar {clause.clause_type} clause detected",
                                same_vendor=contract.party_b == similar_contract.party_b,
                                same_jurisdiction=contract.jurisdiction == similar_contract.jurisdiction,
                                similar_clauses=True
                            )

                            # Sync to Neo4j
                            self.neo4j.create_correlation(
                                contract.id,
                                similar_contract.id,
                                similar["similarity_score"],
                                correlation.correlation_reason
                            )

                            correlations.append({
                                "contract_id": str(similar_contract.id),
                                "correlation_strength": similar["similarity_score"],
                                "reason": correlation.correlation_reason
                            })

            logger.info(f"Detected {len(correlations)} cross-contract correlations")
            return correlations

        except Exception as e:
            logger.error(f"Error detecting correlations: {e}")
            raise

    def get_regional_risk_heatmap(self):
        """
        Get risk breakdown by region for heatmap visualization.

        Returns:
            List of regions with risk scores
        """
        try:
            # Try Neo4j first, fallback to MySQL if it fails
            try:
                regional_data = self.neo4j.get_regional_risk_breakdown()

                # Enhance with MySQL data
                for region_data in regional_data:
                    region = region_data["region"]
                    contracts = ContractRisk.objects.filter(region=region)

                    region_data["total_contracts"] = contracts.count()
                    region_data["high_risk_contracts"] = contracts.filter(
                        overall_risk_score__gte=0.6
                    ).count()

                if regional_data:
                    logger.info(f"Regional heatmap data from Neo4j: {len(regional_data)} regions")
                    return regional_data
            except Exception as neo4j_error:
                logger.warning(f"Neo4j regional query failed, using MySQL fallback: {neo4j_error}")

            # Fallback to MySQL-only aggregation
            from django.db.models import Avg, Count

            regional_data = ContractRisk.objects.values('region').annotate(
                risk=Avg('overall_risk_score'),
                contract_count=Count('id')
            ).filter(region__isnull=False).exclude(region='')

            result = [
                {
                    "region": item['region'],
                    "risk": round(item['risk'], 2),
                    "contract_count": item['contract_count'],
                    "total_contracts": item['contract_count'],
                    "high_risk_contracts": ContractRisk.objects.filter(
                        region=item['region'],
                        overall_risk_score__gte=0.6
                    ).count()
                }
                for item in regional_data
            ]

            logger.info(f"Regional heatmap data from MySQL: {len(result)} regions")
            return result

        except Exception as e:
            logger.error(f"Error getting regional heatmap: {e}")
            raise

    def get_risk_network_graph(self, limit=50):
        """
        Get network graph data for risk propagation visualization.

        Args:
            limit: Maximum nodes to return

        Returns:
            Graph data with nodes and edges
        """
        try:
            # Try Neo4j first, fallback to MySQL if it fails
            try:
                graph_data = self.neo4j.get_risk_network_graph(limit)

                if graph_data and graph_data.get('nodes'):
                    logger.info(f"Risk network graph from Neo4j: {len(graph_data['nodes'])} nodes")
                    return graph_data
            except Exception as neo4j_error:
                logger.warning(f"Neo4j network graph failed, using MySQL fallback: {neo4j_error}")

            # Fallback to MySQL-based network graph using correlations
            nodes = []
            edges = []

            # Get contracts as nodes
            contracts = ContractRisk.objects.select_related('contract', 'party').order_by('-overall_risk_score')[:limit]

            for cr in contracts:
                nodes.append({
                    "id": str(cr.contract.id),
                    "name": cr.contract.original_filename[:30],
                    "type": "contract",
                    "risk_score": cr.overall_risk_score,
                    "region": cr.region,
                    "vendor": cr.party.name if cr.party else "Unknown"
                })

            # Get correlations as edges
            correlations = CrossContractCorrelation.objects.filter(
                contract_a__in=[cr.contract for cr in contracts]
            ).select_related('contract_a', 'contract_b')[:100]

            for corr in correlations:
                edges.append({
                    "source": str(corr.contract_a.id),
                    "target": str(corr.contract_b.id),
                    "strength": corr.correlation_strength,
                    "reason": corr.correlation_reason
                })

            graph_data = {
                "nodes": nodes,
                "edges": edges
            }

            logger.info(f"Risk network graph from MySQL: {len(nodes)} nodes, {len(edges)} edges")
            return graph_data

        except Exception as e:
            logger.error(f"Error getting risk network graph: {e}")
            raise


# Singleton instance
_risk_engine = None


def get_risk_engine():
    """Get or create risk engine instance"""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
