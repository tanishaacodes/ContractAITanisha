"""
Knowledge Graph Service
=======================
Syncs contract data to Neo4j graph database for advanced relationship querying
and visualization.

Graph Schema:
- Nodes: Contract, Clause, Intent, Obligation, Right, Party, Risk
- Relationships: HAS_CLAUSE, CONTAINS_INTENT, HAS_OBLIGATION, HAS_RIGHT,
                 SIMILAR_TO, REFERENCES, PARTY_TO_CONTRACT
"""

import logging
from typing import Dict, List, Optional
from neo4j import GraphDatabase
from django.conf import settings
from core.models import (
    Contract, Clause, Intent, ClauseIntent,
    IntentObligation, IntentRight, ContractRiskAnalysis
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for managing contract knowledge graph in Neo4j"""

    def __init__(self):
        # Neo4j connection settings
        # Default to local Neo4j instance - update in settings.py for production
        self.uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
        self.username = getattr(settings, 'NEO4J_USERNAME', 'neo4j')
        self.password = getattr(settings, 'NEO4J_PASSWORD', 'password')

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Knowledge Graph features disabled.")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def sync_contract_to_graph(self, contract_id: str) -> Dict:
        """
        Sync a contract and all its relationships to Neo4j graph.

        Creates/updates:
        - Contract node
        - Clause nodes
        - Intent nodes
        - Obligation nodes
        - Right nodes
        - All relationships
        """
        if not self.driver:
            return {'success': False, 'error': 'Neo4j not available'}

        try:
            contract = Contract.objects.get(id=contract_id)

            with self.driver.session() as session:
                # Create Contract node
                session.execute_write(self._create_contract_node, contract)

                # Create Clause nodes and relationships
                clauses = Clause.objects.filter(contract=contract, found=True)
                for clause in clauses:
                    session.execute_write(self._create_clause_node, contract, clause)

                # Create Intent nodes and relationships
                clause_intents = ClauseIntent.objects.filter(
                    clause__contract=contract
                ).select_related('clause', 'intent')

                for ci in clause_intents:
                    session.execute_write(self._create_intent_node, contract, ci.clause, ci.intent)

                # Create Obligation nodes and relationships
                intent_obligations = IntentObligation.objects.filter(
                    clause__contract=contract
                ).select_related('clause', 'intent', 'obligation')

                for io in intent_obligations:
                    session.execute_write(
                        self._create_obligation_node,
                        contract, io.intent, io.obligation
                    )

                # Create Right nodes and relationships
                intent_rights = IntentRight.objects.filter(
                    clause__contract=contract
                ).select_related('clause', 'intent', 'right')

                for ir in intent_rights:
                    session.execute_write(
                        self._create_right_node,
                        contract, ir.intent, ir.right
                    )

                # Add risk metadata to contract node
                try:
                    risk_analysis = ContractRiskAnalysis.objects.get(contract=contract)
                    session.execute_write(
                        self._add_risk_metadata,
                        contract, risk_analysis
                    )
                except ContractRiskAnalysis.DoesNotExist:
                    pass

            logger.info(f"Synced contract {contract.id} to knowledge graph")

            return {
                'success': True,
                'contract_id': contract_id,
                'nodes_created': clauses.count() + clause_intents.count() +
                                intent_obligations.count() + intent_rights.count() + 1,
                'message': 'Contract synced to knowledge graph'
            }

        except Contract.DoesNotExist:
            return {'success': False, 'error': 'Contract not found'}
        except Exception as e:
            logger.error(f"Error syncing to graph: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _create_contract_node(tx, contract):
        """Create/update Contract node"""
        query = """
        MERGE (c:Contract {id: $id})
        SET c.filename = $filename,
            c.contractType = $contractType,
            c.uploadedAt = $uploadedAt,
            c.confidenceScore = $confidenceScore,
            c.updatedAt = datetime()
        RETURN c
        """
        tx.run(query,
            id=str(contract.id),
            filename=contract.original_filename,
            contractType=contract.contract_type or 'Unknown',
            uploadedAt=contract.uploaded_at.isoformat() if contract.uploaded_at else None,
            confidenceScore=float(contract.confidence_score) if contract.confidence_score else 0.0
        )

    @staticmethod
    def _create_clause_node(tx, contract, clause):
        """Create/update Clause node and link to Contract"""
        query = """
        MATCH (c:Contract {id: $contractId})
        MERGE (cl:Clause {id: $id})
        SET cl.name = $name,
            cl.confidence = $confidence,
            cl.extractedText = $text,
            cl.updatedAt = datetime()
        MERGE (c)-[:HAS_CLAUSE]->(cl)
        RETURN cl
        """
        tx.run(query,
            contractId=str(contract.id),
            id=str(clause.id),
            name=clause.clause_name,
            confidence=float(clause.confidence) if clause.confidence else 0.0,
            text=(clause.extracted_text or '')[:500]  # Truncate for graph storage
        )

    @staticmethod
    def _create_intent_node(tx, contract, clause, intent):
        """Create/update Intent node and relationships"""
        query = """
        MATCH (c:Contract {id: $contractId})
        MATCH (cl:Clause {id: $clauseId})
        MERGE (i:Intent {id: $id})
        SET i.name = $name,
            i.description = $description,
            i.category = $category,
            i.updatedAt = datetime()
        MERGE (c)-[:CONTAINS_INTENT]->(i)
        MERGE (cl)-[:HAS_INTENT]->(i)
        RETURN i
        """
        tx.run(query,
            contractId=str(contract.id),
            clauseId=str(clause.id),
            id=str(intent.id),
            name=intent.name,
            description=(intent.description or '')[:300],
            category=intent.category or 'General'
        )

    @staticmethod
    def _create_obligation_node(tx, contract, intent, obligation):
        """Create/update Obligation node and relationships"""
        query = """
        MATCH (i:Intent {id: $intentId})
        MERGE (o:Obligation {id: $id})
        SET o.description = $description,
            o.party = $party,
            o.deadline = $deadline,
            o.priority = $priority,
            o.updatedAt = datetime()
        MERGE (i)-[:HAS_OBLIGATION]->(o)
        RETURN o
        """
        tx.run(query,
            intentId=str(intent.id),
            id=str(obligation.id),
            description=(obligation.description or '')[:300],
            party=obligation.party or 'Unknown',
            deadline=obligation.deadline.isoformat() if obligation.deadline else None,
            priority=obligation.priority or 'MEDIUM'
        )

    @staticmethod
    def _create_right_node(tx, contract, intent, right):
        """Create/update Right node and relationships"""
        query = """
        MATCH (i:Intent {id: $intentId})
        MERGE (r:Right {id: $id})
        SET r.description = $description,
            r.party = $party,
            r.updatedAt = datetime()
        MERGE (i)-[:HAS_RIGHT]->(r)
        RETURN r
        """
        tx.run(query,
            intentId=str(intent.id),
            id=str(right.id),
            description=(right.description or '')[:300],
            party=right.party or 'Unknown'
        )

    @staticmethod
    def _add_risk_metadata(tx, contract, risk_analysis):
        """Add risk metadata to Contract node"""
        query = """
        MATCH (c:Contract {id: $contractId})
        SET c.riskLevel = $riskLevel,
            c.riskScore = $riskScore,
            c.totalDeviations = $totalDeviations
        RETURN c
        """
        tx.run(query,
            contractId=str(contract.id),
            riskLevel=risk_analysis.risk_level,
            riskScore=risk_analysis.risk_score,
            totalDeviations=risk_analysis.total_deviations
        )

    def query_graph(self, cypher_query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a custom Cypher query on the graph.

        Example queries:
        - Find all high-risk contracts:
          MATCH (c:Contract) WHERE c.riskLevel = 'HIGH' RETURN c
        - Find contracts with similar intents:
          MATCH (c1:Contract)-[:CONTAINS_INTENT]->(i:Intent)<-[:CONTAINS_INTENT]-(c2:Contract)
          WHERE c1.id = $contractId AND c1 <> c2
          RETURN c2, count(i) as commonIntents
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Graph query error: {str(e)}")
            return []

    def get_contract_subgraph(self, contract_id: str) -> Dict:
        """
        Get the subgraph for a specific contract.
        Returns nodes and edges for visualization.
        """
        if not self.driver:
            return {'nodes': [], 'edges': []}

        query = """
        MATCH (c:Contract {id: $contractId})
        OPTIONAL MATCH (c)-[r1:HAS_CLAUSE]->(cl:Clause)
        OPTIONAL MATCH (cl)-[r2:HAS_INTENT]->(i:Intent)
        OPTIONAL MATCH (i)-[r3:HAS_OBLIGATION]->(o:Obligation)
        OPTIONAL MATCH (i)-[r4:HAS_RIGHT]->(r:Right)
        RETURN c, cl, i, o, r, r1, r2, r3, r4
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, contractId=str(contract_id))

                nodes = []
                edges = []
                node_ids = set()

                for record in result:
                    # Add nodes
                    for key in ['c', 'cl', 'i', 'o', 'r']:
                        node = record.get(key)
                        if node and node.element_id not in node_ids:
                            node_data = dict(node)
                            node_data['type'] = list(node.labels)[0]
                            nodes.append(node_data)
                            node_ids.add(node.element_id)

                    # Add relationships
                    for key in ['r1', 'r2', 'r3', 'r4']:
                        rel = record.get(key)
                        if rel:
                            edges.append({
                                'source': rel.start_node.element_id,
                                'target': rel.end_node.element_id,
                                'type': rel.type
                            })

                return {'nodes': nodes, 'edges': edges}

        except Exception as e:
            logger.error(f"Error getting subgraph: {str(e)}")
            return {'nodes': [], 'edges': []}

    def find_similar_contracts(self, contract_id: str, limit: int = 5) -> List[Dict]:
        """
        Find contracts with similar intents/clauses.
        Uses graph similarity based on common intents.
        """
        if not self.driver:
            return []

        query = """
        MATCH (c1:Contract {id: $contractId})-[:CONTAINS_INTENT]->(i:Intent)
               <-[:CONTAINS_INTENT]-(c2:Contract)
        WHERE c1 <> c2
        WITH c2, count(DISTINCT i) as commonIntents
        MATCH (c2)-[:CONTAINS_INTENT]->(allIntents:Intent)
        WITH c2, commonIntents, count(DISTINCT allIntents) as totalIntents
        RETURN c2.id as contractId,
               c2.filename as filename,
               c2.contractType as contractType,
               commonIntents,
               totalIntents,
               toFloat(commonIntents) / totalIntents as similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, contractId=str(contract_id), limit=limit)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error finding similar contracts: {str(e)}")
            return []
