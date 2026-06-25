# Neo4j Clause Evolution Graph - Setup Guide

## Feature 2: Neo4j Clause Evolution Graph

Track how clauses are born, mutate, succeed, and die using graph database technology.

## What This Feature Provides

- **Clause Lineage Tracking**: See how clauses evolve from version to version
- **Event History**: Track real-world outcomes (EXECUTED, DISPUTED, RENEWED, LITIGATED)
- **Best Version Detection**: Automatically identify the best-performing version
- **Similar Clause Discovery**: Find clauses with similar evolution patterns
- **Root Cause Analysis**: Understand why clauses succeed or fail

## Prerequisites

### Option 1: Neo4j Desktop (Recommended for Development)

1. Download Neo4j Desktop: https://neo4j.com/download/
2. Install and create a new database
3. Start the database
4. Note your connection details (usually `bolt://localhost:7687`)
5. Set a password (default user is `neo4j`)

### Option 2: Neo4j Docker

```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:latest
```

### Option 3: Neo4j Cloud (Aura)

1. Sign up at: https://neo4j.com/cloud/aura/
2. Create a free database
3. Note your connection URI and credentials

## Setup Instructions

### Step 1: Configure Environment Variables

Create or update your `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### Step 2: Initialize Neo4j Schema

```bash
cd backend
python manage.py setup_graph
```

This will:
- ✅ Test Neo4j connection
- ✅ Create constraints and indexes
- ✅ Initialize the graph schema

### Step 3: Sync Clause Data

Sync existing clauses to the graph database:

```bash
python manage.py setup_graph --sync-all
```

Options:
- `--sync-all`: Sync clauses to Neo4j
- `--limit N`: Limit number of clauses to sync (default: 20)

## API Endpoints

### Check Graph Status
```http
GET /api/graph/status/
```

Returns:
```json
{
  "connected": true,
  "uri": "bolt://localhost:7687",
  "stats": {
    "clauses": 20,
    "versions": 20,
    "events": 80
  }
}
```

### Initialize Schema
```http
POST /api/graph/initialize/
```

### Sync All Clauses
```http
POST /api/graph/sync/
```

### Sync Single Clause
```http
POST /api/graph/sync/{clause_id}/
```

### Get Clause Evolution Path
```http
GET /api/graph/evolution/{clause_id}/
```

Returns:
```json
{
  "clause_id": "...",
  "clause_name": "Payment Terms",
  "nodes": [
    {
      "id": "...",
      "version": 1,
      "risk_score": 0.5,
      "text_preview": "Payment shall be made within..."
    }
  ],
  "links": []
}
```

### Get Best Performing Version
```http
GET /api/graph/best-version/{clause_id}/
```

Returns:
```json
{
  "clause_id": "...",
  "best_version": {
    "id": "...",
    "version_number": 2,
    "avg_outcome": 0.85,
    "event_count": 5
  }
}
```

## Graph Schema

### Nodes

- **Clause**: Base clause entity
  - Properties: `id`, `code`, `name`, `status`, `health_score`
- **ClauseVersion**: Specific version of a clause
  - Properties: `id`, `version_number`, `text`, `risk_score`
- **Event**: Real-world outcome
  - Properties: `id`, `type`, `outcome_score`, `jurisdiction`, `counterparty_type`

### Relationships

- `(Clause)-[:HAS_VERSION]->(ClauseVersion)`
- `(ClauseVersion)-[:EVOLVED_FROM {weight}]->(ClauseVersion)`
- `(ClauseVersion)-[:TRIGGERED_EVENT]->(Event)`

## Example Cypher Queries

### Find Clause Evolution Path
```cypher
MATCH path=(c:Clause {id: $clause_id})-[:HAS_VERSION]->(v:ClauseVersion)
OPTIONAL MATCH evolution=(v)-[:EVOLVED_FROM*]->(root)
RETURN v, evolution
ORDER BY v.version_number
```

### Find Best Performing Version
```cypher
MATCH (c:Clause {id: $clause_id})-[:HAS_VERSION]->(v:ClauseVersion)
OPTIONAL MATCH (v)-[:TRIGGERED_EVENT]->(e:Event)
WITH v, avg(e.outcome_score) as avg_outcome, count(e) as event_count
RETURN v, avg_outcome, event_count
ORDER BY avg_outcome DESC
LIMIT 1
```

### Find Similar Clauses
```cypher
MATCH (c1:Clause {id: $clause_id})-[:HAS_VERSION]->(v1:ClauseVersion)
MATCH (c2:Clause)-[:HAS_VERSION]->(v2:ClauseVersion)
WHERE c1 <> c2
AND abs(v1.risk_score - v2.risk_score) < 0.2
RETURN DISTINCT c2
LIMIT 5
```

## Troubleshooting

### Connection Failed
- Ensure Neo4j is running
- Check firewall settings (port 7687)
- Verify credentials in environment variables

### No Data in Graph
- Run `python manage.py setup_graph --sync-all`
- Ensure you have clauses in MySQL first
- Check logs for sync errors

### Permission Denied
- Ensure Neo4j user has write permissions
- Check authentication settings

## Integration with Other Features

### Self-Healing Clause Library
- Evolution graph shows why clauses were promoted/retired
- Tracks success patterns across versions

### Negotiation Heat Engine (Future)
- Graph identifies clauses that trigger disputes
- Predicts negotiation loops based on historical patterns

### Clause Trust Score (Future)
- Graph propagates trust/distrust across related clauses
- Identifies "Silent Killer" clauses with hidden risks

## Next Steps

1. ✅ Feature 2 Complete: Neo4j Clause Evolution Graph
2. ⏭️ Feature 3: Live Clause Co-Pilot (Negotiation Mode)
3. ⏭️ Feature 4: Clause Negotiation Heat Engine
4. ⏭️ Feature 5: Clause Trust Score (CTS)
5. ⏭️ Feature 6: Neo4j Trust Propagation Graph
6. ⏭️ Feature 7: Temporal Clause Evolution Engine

## Resources

- Neo4j Documentation: https://neo4j.com/docs/
- Cypher Query Language: https://neo4j.com/docs/cypher-manual/
- Neo4j Browser: http://localhost:7474 (when running locally)
