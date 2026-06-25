"""
Clause Evolution Graph Sync
Syncs clause data from MySQL to Neo4j for evolution tracking
"""

from .graph_driver import get_neo4j_driver


class ClauseGraphSync:
    """Sync clause evolution data to Neo4j"""

    def __init__(self):
        self.driver = get_neo4j_driver()

    def upsert_clause(self, clause):
        """
        Create or update a Clause node

        Args:
            clause: Clause model instance
        """
        query = """
        MERGE (c:Clause {id: $id})
        SET c.code = $code,
            c.name = $name,
            c.status = $status,
            c.created_at = datetime($created_at)
        RETURN c
        """

        self.driver.run_write_query(query, {
            'id': str(clause.id),
            'code': clause.clause_name or 'Unknown',
            'name': clause.clause_name or 'Unknown',
            'status': 'ACTIVE',  # Will be updated with health metrics
            'created_at': clause.created_at.isoformat() if hasattr(clause, 'created_at') else None
        })

    def upsert_clause_version(self, version, parent_version=None):
        """
        Create or update a ClauseVersion node and link to Clause

        Args:
            version: ClauseVersion model instance
            parent_version: Parent ClauseVersion if this evolved from another
        """
        # Create/update the version node
        query = """
        MATCH (c:Clause {id: $clause_id})
        MERGE (v:ClauseVersion {id: $version_id})
        SET v.version_number = $version_number,
            v.text = $text,
            v.risk_score = $risk_score,
            v.created_at = datetime($created_at)
        MERGE (c)-[:HAS_VERSION]->(v)
        RETURN v
        """

        self.driver.run_write_query(query, {
            'clause_id': str(version.clause.id),
            'version_id': str(version.id),
            'version_number': version.version_number,
            'text': (version.modified_text or version.original_text or '')[:500],  # Truncate for graph
            'risk_score': 0.5,  # Default, will be updated
            'created_at': version.created_at.isoformat() if hasattr(version, 'created_at') else None
        })

        # Link to parent version if evolution
        if parent_version:
            evolution_query = """
            MATCH (parent:ClauseVersion {id: $parent_id})
            MATCH (child:ClauseVersion {id: $child_id})
            MERGE (child)-[:EVOLVED_FROM {weight: 0.8}]->(parent)
            """

            self.driver.run_write_query(evolution_query, {
                'parent_id': str(parent_version.id),
                'child_id': str(version.id)
            })

    def upsert_clause_event(self, event):
        """
        Create or update an Event node and link to ClauseVersion

        Args:
            event: ClauseEvent model instance
        """
        query = """
        MATCH (v:ClauseVersion {id: $version_id})
        CREATE (e:Event {
            id: $event_id,
            type: $event_type,
            outcome_score: $outcome_score,
            jurisdiction: $jurisdiction,
            counterparty_type: $counterparty_type,
            created_at: datetime($created_at)
        })
        MERGE (v)-[:TRIGGERED_EVENT]->(e)
        RETURN e
        """

        self.driver.run_write_query(query, {
            'version_id': str(event.clause_version.id),
            'event_id': str(event.id),
            'event_type': event.event_type,
            'outcome_score': float(event.outcome_score),
            'jurisdiction': event.jurisdiction or 'Unknown',
            'counterparty_type': event.counterparty_type or 'Unknown',
            'created_at': event.created_at.isoformat()
        })

    def update_health_metrics(self, clause, health_metrics):
        """
        Update clause and version nodes with health metrics

        Args:
            clause: Clause model instance
            health_metrics: ClauseHealthMetrics instance
        """
        # Update clause status
        clause_query = """
        MATCH (c:Clause {id: $clause_id})
        SET c.status = $status,
            c.health_score = $health_score
        """

        self.driver.run_write_query(clause_query, {
            'clause_id': str(clause.id),
            'status': health_metrics.status,
            'health_score': float(health_metrics.health_score)
        })

    def sync_clause_family(self, clause):
        """
        Sync entire clause family (all versions and events)

        Args:
            clause: Clause model instance
        """
        from core.models import ClauseVersion, ClauseEvent, ClauseHealthMetrics

        # Sync clause node
        self.upsert_clause(clause)

        # Sync all versions
        versions = ClauseVersion.objects.filter(clause=clause).order_by('version_number')

        prev_version = None
        for version in versions:
            self.upsert_clause_version(version, parent_version=prev_version)

            # Sync events for this version
            events = ClauseEvent.objects.filter(clause_version=version)
            for event in events:
                self.upsert_clause_event(event)

            prev_version = version

        # Sync health metrics if available
        try:
            health_metrics = ClauseHealthMetrics.objects.get(clause=clause)
            self.update_health_metrics(clause, health_metrics)
        except ClauseHealthMetrics.DoesNotExist:
            pass

    def get_clause_evolution_path(self, clause_id):
        """
        Get the evolution path for a clause

        Args:
            clause_id: Clause ID

        Returns:
            List of version nodes in evolution order
        """
        query = """
        MATCH path = (c:Clause {id: $clause_id})-[:HAS_VERSION]->(v:ClauseVersion)
        OPTIONAL MATCH evolution = (v)-[:EVOLVED_FROM*]->(root)
        RETURN v, evolution
        ORDER BY v.version_number
        """

        return self.driver.run_query(query, {'clause_id': str(clause_id)})

    def get_best_performing_version(self, clause_id):
        """
        Find the best performing version of a clause

        Args:
            clause_id: Clause ID

        Returns:
            Best version node data
        """
        query = """
        MATCH (c:Clause {id: $clause_id})-[:HAS_VERSION]->(v:ClauseVersion)
        OPTIONAL MATCH (v)-[:TRIGGERED_EVENT]->(e:Event)
        WITH v, avg(e.outcome_score) as avg_outcome, count(e) as event_count
        RETURN v, avg_outcome, event_count
        ORDER BY avg_outcome DESC, event_count DESC
        LIMIT 1
        """

        results = self.driver.run_query(query, {'clause_id': str(clause_id)})
        return results[0] if results else None

    def find_similar_clause_paths(self, clause_id, similarity_threshold=0.7):
        """
        Find clauses with similar evolution patterns

        Args:
            clause_id: Clause ID
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar clause paths
        """
        # This would use embeddings in production - simplified for now
        query = """
        MATCH (c1:Clause {id: $clause_id})-[:HAS_VERSION]->(v1:ClauseVersion)
        MATCH (c2:Clause)-[:HAS_VERSION]->(v2:ClauseVersion)
        WHERE c1 <> c2
        AND abs(v1.risk_score - v2.risk_score) < 0.2
        RETURN DISTINCT c2, count(v2) as version_count
        LIMIT 5
        """

        return self.driver.run_query(query, {'clause_id': str(clause_id)})


# Singleton instance
_graph_sync = None


def get_graph_sync():
    """Get or create singleton graph sync instance"""
    global _graph_sync
    if _graph_sync is None:
        _graph_sync = ClauseGraphSync()
    return _graph_sync
