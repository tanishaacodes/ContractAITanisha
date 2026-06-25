"""
Neo4j Graph Database Driver
Handles connections to Neo4j for clause evolution tracking
"""

from neo4j import GraphDatabase
import os

class Neo4jDriver:
    """Singleton Neo4j driver for clause evolution graph"""

    def __init__(self):
        # Configuration - update these based on your Neo4j setup
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"[INFO] Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"[WARNING] Neo4j connection failed: {e}")
            print("[INFO] Graph features will be disabled until Neo4j is configured")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def run_query(self, query, parameters=None):
        """
        Execute a Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters dict

        Returns:
            List of result records
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"[ERROR] Neo4j query failed: {e}")
            return []

    def run_write_query(self, query, parameters=None):
        """
        Execute a write query (CREATE, MERGE, DELETE)

        Args:
            query: Cypher query string
            parameters: Query parameters dict

        Returns:
            Query result summary
        """
        if not self.driver:
            return None

        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return result.consume()
        except Exception as e:
            print(f"[ERROR] Neo4j write query failed: {e}")
            return None

    def initialize_schema(self):
        """Create constraints and indexes for optimal performance"""
        if not self.driver:
            return

        # Constraints
        constraints = [
            "CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT version_id IF NOT EXISTS FOR (v:ClauseVersion) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
        ]

        # Indexes
        indexes = [
            "CREATE INDEX clause_code_idx IF NOT EXISTS FOR (c:Clause) ON (c.code)",
            "CREATE INDEX version_health_idx IF NOT EXISTS FOR (v:ClauseVersion) ON (v.health_score)",
            "CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.type)",
        ]

        for constraint in constraints:
            try:
                self.run_write_query(constraint)
            except Exception as e:
                print(f"[WARNING] Constraint creation failed (may already exist): {e}")

        for index in indexes:
            try:
                self.run_write_query(index)
            except Exception as e:
                print(f"[WARNING] Index creation failed (may already exist): {e}")

        print("[INFO] Neo4j schema initialized")


# Singleton instance
_neo4j_driver = None


def get_neo4j_driver():
    """Get or create singleton Neo4j driver"""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver()
    return _neo4j_driver
