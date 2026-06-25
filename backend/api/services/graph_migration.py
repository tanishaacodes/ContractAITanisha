"""
Graph Migration Utility
========================
Migrate contract graphs between NetworkX (in-memory) and Neo4j (persistent).

Usage:
    python manage.py shell
    >>> from api.services.graph_migration import migrate_all_contracts_to_neo4j
    >>> migrate_all_contracts_to_neo4j()
"""

import logging
from typing import List, Dict, Any
import networkx as nx

from core.models import Contract, Clause
from .graph_builder import build_contract_graph
from .neo4j_graph_service import Neo4jGraphService

logger = logging.getLogger(__name__)


class GraphMigration:
    """Migrate graphs between NetworkX and Neo4j"""

    def __init__(self):
        self.neo4j_service = Neo4jGraphService()

    def migrate_contract_to_neo4j(self, contract_id: str) -> Dict[str, Any]:
        """
        Migrate a single contract's graph to Neo4j.

        Args:
            contract_id: Contract UUID

        Returns:
            Dict with migration result
        """
        try:
            # Get contract and clauses
            try:
                contract = Contract.objects.get(id=contract_id)
                clauses = list(Clause.objects.filter(contract=contract))
            except Contract.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Contract {contract_id} not found'
                }

            if not clauses:
                return {
                    'success': False,
                    'error': 'No clauses found for contract'
                }

            # Build NetworkX graph
            nx_graph = build_contract_graph(clauses)

            # Extract edges
            edges = []
            for source, target, data in nx_graph.edges(data=True):
                edges.append((source, target, data))

            # Create in Neo4j
            success = self.neo4j_service.create_contract_graph(
                contract_id=str(contract_id),
                clauses=clauses,
                edges=edges
            )

            if success:
                logger.info(f"[MIGRATION] Successfully migrated contract {contract_id} to Neo4j")
                return {
                    'success': True,
                    'contract_id': str(contract_id),
                    'nodes': len(nx_graph.nodes),
                    'edges': len(nx_graph.edges)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create graph in Neo4j'
                }

        except Exception as e:
            logger.error(f"[MIGRATION] Error migrating contract {contract_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def migrate_all_contracts_to_neo4j(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Migrate all contracts to Neo4j.

        Args:
            batch_size: Number of contracts to process at once

        Returns:
            Dict with migration summary
        """
        if not self.neo4j_service.neo4j_available:
            return {
                'success': False,
                'error': 'Neo4j not available'
            }

        try:
            contracts = Contract.objects.all()
            total = contracts.count()

            results = {
                'total_contracts': total,
                'successful': 0,
                'failed': 0,
                'errors': []
            }

            logger.info(f"[MIGRATION] Starting migration of {total} contracts")

            for i, contract in enumerate(contracts):
                logger.info(f"[MIGRATION] Processing contract {i+1}/{total}: {contract.id}")

                result = self.migrate_contract_to_neo4j(str(contract.id))

                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'contract_id': str(contract.id),
                        'error': result.get('error')
                    })

                # Log progress
                if (i + 1) % batch_size == 0:
                    logger.info(
                        f"[MIGRATION] Progress: {i+1}/{total} "
                        f"(Success: {results['successful']}, Failed: {results['failed']})"
                    )

            logger.info(
                f"[MIGRATION] Completed: {results['successful']}/{total} successful, "
                f"{results['failed']} failed"
            )

            results['success'] = True
            return results

        except Exception as e:
            logger.error(f"[MIGRATION] Error during batch migration: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def verify_migration(self, contract_id: str) -> Dict[str, Any]:
        """
        Verify that a contract's graph was migrated correctly.

        Args:
            contract_id: Contract UUID

        Returns:
            Dict with verification result
        """
        try:
            # Get clauses
            contract = Contract.objects.get(id=contract_id)
            clauses = list(Clause.objects.filter(contract=contract))

            # Build NetworkX graph
            nx_graph = build_contract_graph(clauses)

            # Get from Neo4j
            neo4j_graph = self.neo4j_service.get_contract_graph(str(contract_id))

            if neo4j_graph is None:
                return {
                    'success': False,
                    'error': 'Graph not found in Neo4j'
                }

            # Compare
            nx_nodes = len(nx_graph.nodes)
            nx_edges = len(nx_graph.edges)
            neo4j_nodes = len(neo4j_graph.nodes)
            neo4j_edges = len(neo4j_graph.edges)

            is_valid = (nx_nodes == neo4j_nodes) and (nx_edges == neo4j_edges)

            return {
                'success': True,
                'valid': is_valid,
                'networkx': {
                    'nodes': nx_nodes,
                    'edges': nx_edges
                },
                'neo4j': {
                    'nodes': neo4j_nodes,
                    'edges': neo4j_edges
                }
            }

        except Exception as e:
            logger.error(f"[MIGRATION] Error verifying migration: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions
def migrate_all_contracts_to_neo4j() -> Dict[str, Any]:
    """Migrate all contracts to Neo4j"""
    migration = GraphMigration()
    return migration.migrate_all_contracts_to_neo4j()


def migrate_contract_to_neo4j(contract_id: str) -> Dict[str, Any]:
    """Migrate a single contract to Neo4j"""
    migration = GraphMigration()
    return migration.migrate_contract_to_neo4j(contract_id)


def verify_migration(contract_id: str) -> Dict[str, Any]:
    """Verify migration for a contract"""
    migration = GraphMigration()
    return migration.verify_migration(contract_id)
