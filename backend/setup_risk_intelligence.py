#!/usr/bin/env python
"""
Risk Intelligence Setup Script
==============================
Initializes Neo4j graph schema for Risk Intelligence feature.

Usage:
    python setup_risk_intelligence.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.graph.risk_graph_schema import get_risk_graph_schema


def main():
    print("=" * 60)
    print("Risk Intelligence Setup")
    print("=" * 60)

    # Get schema instance
    schema = get_risk_graph_schema()

    # Check Neo4j connection
    print("\n[1/4] Checking Neo4j connection...")
    if not schema.connected:
        print("❌ ERROR: Neo4j is not connected!")
        print("\nTroubleshooting:")
        print("1. Ensure Neo4j Docker container is running:")
        print("   docker ps | grep neo4j")
        print("\n2. If not running, start it:")
        print("   docker run -d -p 7687:7687 -p 7474:7474 \\")
        print("     -e NEO4J_AUTH=neo4j/password \\")
        print("     --name neo4j neo4j:5")
        print("\n3. Check .env file has correct credentials:")
        print("   NEO4J_URI=bolt://localhost:7687")
        print("   NEO4J_USER=neo4j")
        print("   NEO4J_PASSWORD=password")
        return 1

    print("✅ Neo4j connected successfully!")

    # Apply schema
    print("\n[2/4] Applying graph schema (constraints & indices)...")
    if schema.apply_schema():
        print("✅ Schema applied successfully!")
    else:
        print("⚠️  Schema application failed (constraints may already exist)")

    # Seed risk categories
    print("\n[3/4] Seeding risk categories...")
    if schema.seed_risk_categories():
        print("✅ 10 risk categories seeded:")
        print("   - INDEMNITY, LIABILITY, TERMINATION, PAYMENT")
        print("   - CONFIDENTIALITY, INTELLECTUAL_PROPERTY, WARRANTY")
        print("   - COMPLIANCE, DISPUTE_RESOLUTION, FORCE_MAJEURE")
    else:
        print("⚠️  Risk seeding failed")

    # Seed jurisdictions
    print("\n[4/4] Seeding jurisdictions...")
    if schema.seed_jurisdictions():
        print("✅ 9 jurisdictions seeded:")
        print("   - US-NY, US-CA, US-DE, IN, UK, SG, HK, UAE, EU")
    else:
        print("⚠️  Jurisdiction seeding failed")

    print("\n" + "=" * 60)
    print("✅ Risk Intelligence setup complete!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Start backend server:")
    print("   cd backend && python manage.py runserver 8002")
    print("\n2. Access Risk Intelligence Dashboard:")
    print("   http://localhost:3000/risk-intelligence/<contract-id>")
    print("\n3. Or use API endpoints:")
    print("   POST /api/risk-intelligence/monte-carlo")
    print("   POST /api/risk-intelligence/var")
    print("   POST /api/risk-intelligence/stress-test")
    print("   GET  /api/risk-intelligence/risk-subgraph/<contract-id>")

    return 0


if __name__ == '__main__':
    sys.exit(main())
