"""
Neo4j Graph Database Service
Handles all Neo4j operations for cross-contract risk analysis
"""
from neo4j import GraphDatabase
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """
    Service class for Neo4j graph database operations.
    Manages driver lifecycle and provides graph operations.
    """

    def __init__(self):
        """Initialize Neo4j driver connection"""
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info(f"Neo4j driver initialized with URI: {settings.NEO4J_URI}")

    def close(self):
        """Close the Neo4j driver"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")

    def verify_connection(self):
        """Verify Neo4j connection is working"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connection verification failed: {e}")
            return False

    # =================================================================
    # SCHEMA SETUP & INDEXES
    # =================================================================

    def create_indexes(self):
        """Create Neo4j indexes for optimal query performance"""
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX contract_id IF NOT EXISTS FOR (c:Contract) ON (c.id)",
                "CREATE INDEX contract_region IF NOT EXISTS FOR (c:Contract) ON (c.region)",
                "CREATE INDEX contract_business_unit IF NOT EXISTS FOR (c:Contract) ON (c.business_unit)",
                "CREATE INDEX party_id IF NOT EXISTS FOR (p:Party) ON (p.id)",
                "CREATE INDEX party_name IF NOT EXISTS FOR (p:Party) ON (p.name)",
                "CREATE INDEX clause_id IF NOT EXISTS FOR (cl:Clause) ON (cl.id)",
                "CREATE INDEX clause_hash IF NOT EXISTS FOR (cl:Clause) ON (cl.hash)",
                "CREATE INDEX risk_id IF NOT EXISTS FOR (r:Risk) ON (r.id)",
                "CREATE INDEX partition_key IF NOT EXISTS FOR (pp:PartyPartition) ON (pp.key)"
            ]

            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"Created index: {index_query}")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")

    # =================================================================
    # CONTRACT OPERATIONS
    # =================================================================

    def upsert_contract(self, contract_id, value, region, business_unit, risk_score=0.0):
        """
        Create or update a Contract node in Neo4j.

        Args:
            contract_id: Contract UUID
            value: Contract monetary value
            region: Geographic region (APAC, EMEA, US)
            business_unit: Business unit (Finance, IT, etc.)
            risk_score: Overall risk score (0-1)
        """
        query = """
        MERGE (c:Contract {id: $id})
        SET c.value = $value,
            c.region = $region,
            c.business_unit = $business_unit,
            c.risk_score = $risk_score,
            c.updated_at = datetime()
        RETURN c
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                id=str(contract_id),
                value=float(value) if value else 0.0,
                region=region,
                business_unit=business_unit,
                risk_score=float(risk_score)
            )
            logger.info(f"Upserted contract node: {contract_id}")
            return result.single()

    # =================================================================
    # PARTY OPERATIONS
    # =================================================================

    def upsert_party(self, party_id, name, party_type, country=None):
        """
        Create or update a Party (vendor/customer) node.

        Args:
            party_id: Party UUID
            name: Party name
            party_type: VENDOR, CUSTOMER, or PARTNER
            country: Country of operation
        """
        query = """
        MERGE (p:Party {id: $id})
        SET p.name = $name,
            p.type = $type,
            p.country = $country,
            p.updated_at = datetime()
        RETURN p
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                id=str(party_id),
                name=name,
                type=party_type,
                country=country
            )
            logger.info(f"Upserted party node: {name}")
            return result.single()

    def upsert_party_partition(self, partition_key, party_id, year, region=None):
        """
        Create or update a PartyPartition node to avoid supernodes.

        Args:
            partition_key: Unique partition key (e.g., "VendorABC_2025")
            party_id: Party UUID
            year: Year of partition
            region: Optional region filter
        """
        query = """
        MERGE (pp:PartyPartition {key: $key})
        SET pp.year = $year,
            pp.region = $region,
            pp.updated_at = datetime()
        WITH pp
        MATCH (p:Party {id: $party_id})
        MERGE (pp)-[:PART_OF]->(p)
        RETURN pp
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                key=partition_key,
                party_id=str(party_id),
                year=int(year),
                region=region
            )
            logger.info(f"Upserted party partition: {partition_key}")
            return result.single()

    # =================================================================
    # CLAUSE OPERATIONS
    # =================================================================

    def upsert_clause(self, clause_hash, category, base_risk):
        """
        Create or update a canonical Clause node.

        Args:
            clause_hash: SHA256 hash of clause text (for deduplication)
            category: Clause category (Indemnity, Liability, SLA, etc.)
            base_risk: Base risk score for this clause type (0-1)
        """
        query = """
        MERGE (cl:Clause {hash: $hash})
        SET cl.category = $category,
            cl.base_risk = $base_risk,
            cl.updated_at = datetime()
        RETURN cl
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                hash=clause_hash,
                category=category,
                base_risk=float(base_risk)
            )
            logger.info(f"Upserted clause node: {category} ({clause_hash[:8]})")
            return result.single()

    def link_contract_clause(self, contract_id, clause_hash, local_risk, negotiated=False):
        """
        Create HAS_CLAUSE relationship between Contract and Clause.

        Args:
            contract_id: Contract UUID
            clause_hash: Clause hash
            local_risk: Clause-specific risk score (0-1)
            negotiated: Whether clause was negotiated
        """
        query = """
        MATCH (c:Contract {id: $contract_id})
        MATCH (cl:Clause {hash: $clause_hash})
        MERGE (c)-[r:HAS_CLAUSE]->(cl)
        SET r.local_risk = $local_risk,
            r.negotiated = $negotiated,
            r.updated_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                contract_id=str(contract_id),
                clause_hash=clause_hash,
                local_risk=float(local_risk),
                negotiated=negotiated
            )
            logger.info(f"Linked contract {contract_id} to clause {clause_hash[:8]}")
            return result.single()

    # =================================================================
    # RISK OPERATIONS
    # =================================================================

    def upsert_risk_node(self, risk_id, risk_type, severity):
        """
        Create or update a Risk node.

        Args:
            risk_id: Risk UUID
            risk_type: LEGAL, FINANCIAL, REGULATORY, OPERATIONAL
            severity: Risk severity (0-1)
        """
        query = """
        MERGE (r:Risk {id: $id})
        SET r.type = $type,
            r.severity = $severity,
            r.updated_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                id=str(risk_id),
                type=risk_type,
                severity=float(severity)
            )
            logger.info(f"Upserted risk node: {risk_type}")
            return result.single()

    def link_clause_risk(self, clause_hash, risk_id):
        """
        Create CREATES_RISK relationship between Clause and Risk.

        Args:
            clause_hash: Clause hash
            risk_id: Risk UUID
        """
        query = """
        MATCH (cl:Clause {hash: $clause_hash})
        MATCH (r:Risk {id: $risk_id})
        MERGE (cl)-[:CREATES_RISK]->(r)
        RETURN cl, r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                clause_hash=clause_hash,
                risk_id=str(risk_id)
            )
            return result.single()

    # =================================================================
    # PARTY-CONTRACT RELATIONSHIPS
    # =================================================================

    def link_party_contract(self, party_id, partition_key, contract_id, year):
        """
        Link Party to Contract through PartyPartition (anti-supernode pattern).

        Args:
            party_id: Party UUID
            partition_key: Partition key (e.g., "VendorABC_2025")
            contract_id: Contract UUID
            year: Year of contract
        """
        query = """
        MATCH (p:Party {id: $party_id})
        MERGE (pp:PartyPartition {key: $partition_key})
        ON CREATE SET pp.year = $year
        MERGE (pp)-[:PART_OF]->(p)
        WITH pp
        MATCH (c:Contract {id: $contract_id})
        MERGE (pp)-[:INVOLVES]->(c)
        RETURN pp, c
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                party_id=str(party_id),
                partition_key=partition_key,
                contract_id=str(contract_id),
                year=int(year)
            )
            logger.info(f"Linked party to contract via partition: {partition_key}")
            return result.single()

    # =================================================================
    # CROSS-CONTRACT CORRELATIONS
    # =================================================================

    def create_correlation(self, contract_a_id, contract_b_id, strength, reason):
        """
        Create CORRELATED_RISK relationship between two contracts.

        Args:
            contract_a_id: First contract UUID
            contract_b_id: Second contract UUID
            strength: Correlation strength (0-1)
            reason: Why contracts are correlated
        """
        query = """
        MATCH (c1:Contract {id: $contract_a_id})
        MATCH (c2:Contract {id: $contract_b_id})
        MERGE (c1)-[r:CORRELATED_RISK]-(c2)
        SET r.strength = $strength,
            r.reason = $reason,
            r.updated_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                contract_a_id=str(contract_a_id),
                contract_b_id=str(contract_b_id),
                strength=float(strength),
                reason=reason
            )
            logger.info(f"Created correlation between contracts: {strength:.2f}")
            return result.single()

    # =================================================================
    # RISK ANALYSIS QUERIES
    # =================================================================

    def get_vendor_exposure(self, vendor_name, region=None):
        """
        Calculate total risk exposure for a vendor.

        Args:
            vendor_name: Vendor name
            region: Optional region filter (APAC, EMEA, US)

        Returns:
            Total exposure score
        """
        if region:
            query = """
            MATCH (p:Party {name: $vendor})-[:PART_OF]->(:PartyPartition)
                  -[:INVOLVES]->(c:Contract {region: $region})
                  -[hc:HAS_CLAUSE]->()
            RETURN sum(hc.local_risk * c.value) AS exposure
            """
            params = {"vendor": vendor_name, "region": region}
        else:
            query = """
            MATCH (p:Party {name: $vendor})-[:PART_OF]->(:PartyPartition)
                  -[:INVOLVES]->(c:Contract)
                  -[hc:HAS_CLAUSE]->()
            RETURN sum(hc.local_risk * c.value) AS exposure
            """
            params = {"vendor": vendor_name}

        with self.driver.session() as session:
            result = session.run(query, **params)
            record = result.single()
            exposure = record["exposure"] if record and record["exposure"] else 0.0
            logger.info(f"Vendor exposure for {vendor_name}: {exposure}")
            return exposure

    def get_regional_risk_breakdown(self):
        """
        Get risk breakdown by region for heatmap.

        Returns:
            List of {region, risk_score, contract_count}
        """
        query = """
        MATCH (c:Contract)-[hc:HAS_CLAUSE]->()
        WHERE c.region IS NOT NULL
        WITH c.region AS region,
             avg(hc.local_risk) AS avg_risk,
             count(DISTINCT c) AS contract_count
        RETURN region, avg_risk AS risk, contract_count
        ORDER BY risk DESC
        """

        with self.driver.session() as session:
            result = session.run(query)
            breakdown = []
            for record in result:
                breakdown.append({
                    "region": record["region"],
                    "risk": float(record["risk"]),
                    "contract_count": record["contract_count"]
                })
            logger.info(f"Regional risk breakdown: {len(breakdown)} regions")
            return breakdown

    def get_risk_network_graph(self, limit=50):
        """
        Get network graph data for visualization.

        Args:
            limit: Maximum number of nodes to return

        Returns:
            Dictionary with nodes and edges for visualization
        """
        query = """
        MATCH (c1:Contract)-[r:CORRELATED_RISK]-(c2:Contract)
        WHERE r.strength > 0.5
        RETURN c1.id AS from, c2.id AS to, r.strength AS weight,
               c1.risk_score AS from_risk, c2.risk_score AS to_risk
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, limit=limit)

            nodes = {}
            edges = []

            for record in result:
                from_id = record["from"]
                to_id = record["to"]

                # Add nodes
                if from_id not in nodes:
                    nodes[from_id] = {
                        "id": from_id,
                        "type": "Contract",
                        "risk": record["from_risk"]
                    }
                if to_id not in nodes:
                    nodes[to_id] = {
                        "id": to_id,
                        "type": "Contract",
                        "risk": record["to_risk"]
                    }

                # Add edge
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "weight": record["weight"]
                })

            graph = {
                "nodes": list(nodes.values()),
                "edges": edges
            }

            logger.info(f"Risk network graph: {len(nodes)} nodes, {len(edges)} edges")
            return graph


# Singleton instance
_neo4j_service = None


def get_neo4j_service():
    """Get or create Neo4j service instance"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service


def close_neo4j_service():
    """Close Neo4j service connection"""
    global _neo4j_service
    if _neo4j_service:
        _neo4j_service.close()
        _neo4j_service = None
