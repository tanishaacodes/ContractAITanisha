"""
Celery tasks for async risk analysis
Handles background processing for contract risk scoring and batch operations
"""
from celery import shared_task, group, chord
from django.core.cache import cache
from django.db import transaction
import logging
from typing import List, Dict, Any

from core.models import Contract
from .models import ContractRisk, VendorExposure
from .services import get_risk_engine

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='risk.analyze_contract')
def analyze_contract_async(self, contract_id: str) -> Dict[str, Any]:
    """
    Async task to analyze a single contract's risk

    Args:
        contract_id: UUID of the contract to analyze

    Returns:
        dict with analysis results
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting analysis...'}
        )

        contract = Contract.objects.get(id=contract_id)
        risk_engine = get_risk_engine()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Scoring clauses...'}
        )

        # Perform analysis
        result = risk_engine.analyze_contract_risk(contract)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Syncing to Neo4j...'}
        )

        # Invalidate cache
        cache.delete(f'contract_risk_{contract_id}')
        cache.delete('portfolio_overview')

        logger.info(f"Successfully analyzed contract {contract_id}")

        return {
            'contract_id': contract_id,
            'risk_score': result.get('overall_risk_score', 0.0),
            'status': 'completed',
            'clauses_analyzed': result.get('clauses_analyzed', 0)
        }

    except Contract.DoesNotExist:
        logger.error(f"Contract {contract_id} not found")
        return {'contract_id': contract_id, 'status': 'error', 'error': 'Contract not found'}
    except Exception as e:
        logger.exception(f"Error analyzing contract {contract_id}: {str(e)}")
        return {'contract_id': contract_id, 'status': 'error', 'error': str(e)}


@shared_task(name='risk.batch_analyze_contracts')
def batch_analyze_contracts(contract_ids: List[str]) -> Dict[str, Any]:
    """
    Analyze multiple contracts in parallel using Celery groups

    Args:
        contract_ids: List of contract UUIDs to analyze

    Returns:
        dict with batch job info
    """
    # Create a group of parallel tasks
    job = group(analyze_contract_async.s(cid) for cid in contract_ids)
    result = job.apply_async()

    return {
        'job_id': result.id,
        'total_contracts': len(contract_ids),
        'status': 'processing'
    }


@shared_task(name='risk.detect_correlations')
def detect_correlations_async(contract_id: str, similarity_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Detect cross-contract correlations asynchronously

    Args:
        contract_id: UUID of the contract
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        dict with detected correlations
    """
    try:
        contract = Contract.objects.get(id=contract_id)
        risk_engine = get_risk_engine()

        # Detect correlations
        correlations = risk_engine.detect_cross_contract_correlations(
            contract,
            similarity_threshold=similarity_threshold
        )

        # Invalidate cache
        cache.delete(f'correlations_{contract_id}')

        logger.info(f"Detected {len(correlations)} correlations for contract {contract_id}")

        return {
            'contract_id': contract_id,
            'correlations_found': len(correlations),
            'status': 'completed'
        }

    except Exception as e:
        logger.exception(f"Error detecting correlations for {contract_id}: {str(e)}")
        return {'contract_id': contract_id, 'status': 'error', 'error': str(e)}


@shared_task(name='risk.update_vendor_exposure')
def update_vendor_exposure_async(vendor_name: str) -> Dict[str, Any]:
    """
    Recompute vendor exposure metrics asynchronously

    Args:
        vendor_name: Name of the vendor/party

    Returns:
        dict with updated exposure metrics
    """
    try:
        from .services.neo4j import get_neo4j_service

        neo4j_service = get_neo4j_service()
        exposure_data = neo4j_service.get_vendor_exposure(vendor_name)

        if not exposure_data:
            return {'vendor': vendor_name, 'status': 'no_data'}

        # Update or create VendorExposure record
        from .models import Party
        party, _ = Party.objects.get_or_create(
            name=vendor_name,
            defaults={'party_type': 'VENDOR'}
        )

        VendorExposure.objects.update_or_create(
            party=party,
            defaults={
                'total_exposure': exposure_data.get('total_exposure', 0.0),
                'contract_count': exposure_data.get('contract_count', 0),
                'average_risk': exposure_data.get('average_risk', 0.0),
                'exposure_by_region': exposure_data.get('by_region', {})
            }
        )

        # Invalidate cache
        cache.delete(f'vendor_exposure_{vendor_name}')
        cache.delete('top_vendor_exposure')

        logger.info(f"Updated vendor exposure for {vendor_name}")

        return {
            'vendor': vendor_name,
            'total_exposure': exposure_data.get('total_exposure', 0.0),
            'status': 'completed'
        }

    except Exception as e:
        logger.exception(f"Error updating vendor exposure for {vendor_name}: {str(e)}")
        return {'vendor': vendor_name, 'status': 'error', 'error': str(e)}


@shared_task(name='risk.refresh_portfolio_metrics')
def refresh_portfolio_metrics() -> Dict[str, Any]:
    """
    Refresh all portfolio-level metrics (run periodically)

    Returns:
        dict with refresh status
    """
    try:
        from .services.neo4j import get_neo4j_service

        neo4j_service = get_neo4j_service()

        # Get all unique vendors from Neo4j
        query = """
        MATCH (p:Party)
        RETURN DISTINCT p.name AS vendor
        """
        result = neo4j_service.execute_query(query)
        vendors = [record['vendor'] for record in result if record['vendor']]

        # Update exposure for all vendors
        tasks = [update_vendor_exposure_async.s(vendor) for vendor in vendors]
        job = group(tasks)
        job.apply_async()

        # Invalidate global caches
        cache.delete('portfolio_overview')
        cache.delete('regional_heatmap')

        logger.info(f"Triggered portfolio refresh for {len(vendors)} vendors")

        return {
            'vendors_updated': len(vendors),
            'status': 'completed'
        }

    except Exception as e:
        logger.exception(f"Error refreshing portfolio metrics: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='risk.scenario_simulation')
def scenario_simulation_async(scenario_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run risk scenario simulation (what-if analysis)

    Args:
        scenario_params: dict with simulation parameters
            - scenario_type: 'vendor_loss', 'jurisdiction_change', 'clause_modification'
            - vendor_name: for vendor_loss scenarios
            - jurisdiction: for jurisdiction_change
            - risk_multiplier: multiplier for risk scores

    Returns:
        dict with simulation results
    """
    try:
        from .services.neo4j import get_neo4j_service

        neo4j_service = get_neo4j_service()
        scenario_type = scenario_params.get('scenario_type')

        if scenario_type == 'vendor_loss':
            # Simulate vendor becoming unavailable
            vendor = scenario_params.get('vendor_name')
            query = """
            MATCH (p:Party {name: $vendor})-[:PART_OF]->(:PartyPartition)
                  -[:INVOLVES]->(c:Contract)
            RETURN count(c) AS affected_contracts,
                   sum(c.risk_score * c.value) AS total_exposure
            """
            result = neo4j_service.execute_query(query, vendor=vendor)

        elif scenario_type == 'risk_multiplier':
            # Apply risk multiplier to specific region/vendor
            multiplier = scenario_params.get('risk_multiplier', 1.0)
            region = scenario_params.get('region')

            query = """
            MATCH (c:Contract {region: $region})
            RETURN count(c) AS affected_contracts,
                   sum(c.risk_score * $multiplier * c.value) AS projected_exposure,
                   sum(c.risk_score * c.value) AS current_exposure
            """
            result = neo4j_service.execute_query(
                query,
                region=region,
                multiplier=multiplier
            )

        else:
            return {'status': 'error', 'error': 'Unknown scenario type'}

        logger.info(f"Completed scenario simulation: {scenario_type}")

        return {
            'scenario_type': scenario_type,
            'results': list(result),
            'status': 'completed'
        }

    except Exception as e:
        logger.exception(f"Error in scenario simulation: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True, name='risk.systemic_risk_detection')
def systemic_risk_detection_async(self) -> Dict[str, Any]:
    """
    Detect systemic risks across the entire portfolio
    Identifies clusters, concentrations, and hidden correlations

    Returns:
        dict with systemic risk findings
    """
    try:
        from .services.neo4j import get_neo4j_service

        self.update_state(state='PROGRESS', meta={'status': 'Analyzing vendor concentration...'})

        neo4j_service = get_neo4j_service()

        # 1. Vendor concentration risk
        vendor_concentration_query = """
        MATCH (p:Party)-[:PART_OF]->(:PartyPartition)-[:INVOLVES]->(c:Contract)
        WITH p.name AS vendor,
             count(c) AS contract_count,
             sum(c.value) AS total_value,
             avg(c.risk_score) AS avg_risk
        WHERE contract_count > 5
        RETURN vendor, contract_count, total_value, avg_risk
        ORDER BY total_value DESC
        LIMIT 20
        """

        vendor_risks = neo4j_service.execute_query(vendor_concentration_query)

        self.update_state(state='PROGRESS', meta={'status': 'Detecting risk clusters...'})

        # 2. Correlated risk clusters
        cluster_query = """
        MATCH (c1:Contract)-[r:CORRELATED_RISK]->(c2:Contract)
        WHERE r.strength > 0.7
        WITH c1, count(r) AS correlation_count
        WHERE correlation_count > 3
        RETURN c1.id AS contract_id,
               c1.risk_score AS risk_score,
               correlation_count
        ORDER BY correlation_count DESC
        LIMIT 10
        """

        risk_clusters = neo4j_service.execute_query(cluster_query)

        self.update_state(state='PROGRESS', meta={'status': 'Analyzing jurisdiction risks...'})

        # 3. Jurisdiction concentration
        jurisdiction_query = """
        MATCH (c:Contract)
        WITH c.jurisdiction AS jurisdiction,
             count(c) AS contract_count,
             sum(c.value) AS total_exposure,
             avg(c.risk_score) AS avg_risk
        WHERE jurisdiction IS NOT NULL
        RETURN jurisdiction, contract_count, total_exposure, avg_risk
        ORDER BY total_exposure DESC
        """

        jurisdiction_risks = neo4j_service.execute_query(jurisdiction_query)

        findings = {
            'vendor_concentration': list(vendor_risks),
            'risk_clusters': list(risk_clusters),
            'jurisdiction_concentration': list(jurisdiction_risks),
            'status': 'completed'
        }

        # Cache results for 1 hour
        cache.set('systemic_risk_findings', findings, timeout=3600)

        logger.info("Completed systemic risk detection")

        return findings

    except Exception as e:
        logger.exception(f"Error in systemic risk detection: {str(e)}")
        return {'status': 'error', 'error': str(e)}
