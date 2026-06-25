#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Populate Sample Graph Data
===========================
Adds beautiful sample nodes and edges for graph visualization demo.
"""

import os
import sys
import django
import uuid
from datetime import datetime

# Setup Django
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.graph.risk_graph_schema import get_risk_graph_schema

print("=" * 80)
print("POPULATING SAMPLE GRAPH DATA FOR BEAUTIFUL VISUALIZATION")
print("=" * 80)

# Get schema
schema = get_risk_graph_schema()

if not schema.connected:
    print("\n[X] Neo4j not connected!")
    print("   Make sure Neo4j is running: docker ps | grep neo4j")
    sys.exit(1)

print("\n[OK] Neo4j connected!")

# Apply schema first
print("\n[1/4] Applying schema...")
try:
    schema.apply_schema()
    print("   [OK] Schema applied")
except Exception as e:
    print(f"   [WARN]  Schema may already exist: {e}")

# Seed base data
print("\n[2/4] Seeding risk categories...")
try:
    schema.seed_risk_categories()
    print("   [OK] Risk categories seeded")
except Exception as e:
    print(f"   [WARN]  Risks may already exist: {e}")

print("\n[3/4] Seeding jurisdictions...")
try:
    schema.seed_jurisdictions()
    print("   [OK] Jurisdictions seeded")
except Exception as e:
    print(f"   [WARN]  Jurisdictions may already exist: {e}")

# Create sample contracts with rich clause data
print("\n[4/4] Creating sample contracts with diverse clauses...")

# Sample Contract 1: Software Development Agreement
contract1_id = str(uuid.uuid4())
contract1_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Scope of Services',
        'clause_type': 'general',
        'risk_score': 0.3,
        'breach_probability': 0.05,
        'loss_mean': 10000.0,
        'loss_std': 2000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Payment Milestones',
        'clause_type': 'payment',
        'risk_score': 0.65,
        'breach_probability': 0.15,
        'loss_mean': 50000.0,
        'loss_std': 10000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Intellectual Property Rights',
        'clause_type': 'intellectual property',
        'risk_score': 0.75,
        'breach_probability': 0.20,
        'loss_mean': 100000.0,
        'loss_std': 20000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Confidentiality Obligations',
        'clause_type': 'confidentiality',
        'risk_score': 0.70,
        'breach_probability': 0.18,
        'loss_mean': 75000.0,
        'loss_std': 15000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Termination for Convenience',
        'clause_type': 'termination',
        'risk_score': 0.55,
        'breach_probability': 0.12,
        'loss_mean': 30000.0,
        'loss_std': 8000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Limitation of Liability',
        'clause_type': 'liability',
        'risk_score': 0.80,
        'breach_probability': 0.25,
        'loss_mean': 150000.0,
        'loss_std': 30000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Warranty Period',
        'clause_type': 'warranty',
        'risk_score': 0.60,
        'breach_probability': 0.14,
        'loss_mean': 40000.0,
        'loss_std': 10000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Dispute Resolution',
        'clause_type': 'dispute resolution',
        'risk_score': 0.50,
        'breach_probability': 0.10,
        'loss_mean': 25000.0,
        'loss_std': 5000.0
    },
]

print("\n   Creating Contract 1: Software Development Agreement")
print(f"   Contract ID: {contract1_id}")
print(f"   Clauses: {len(contract1_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract1_id,
    clauses=contract1_clauses,
    jurisdiction='US'
)
if success:
    print("   [OK] Contract 1 created successfully")
else:
    print("   [FAIL] Contract 1 creation failed")

# Sample Contract 2: Master Services Agreement
contract2_id = str(uuid.uuid4())
contract2_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Service Level Agreement',
        'clause_type': 'general',
        'risk_score': 0.70,
        'breach_probability': 0.18,
        'loss_mean': 60000.0,
        'loss_std': 12000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Payment Terms Net-30',
        'clause_type': 'payment',
        'risk_score': 0.45,
        'breach_probability': 0.08,
        'loss_mean': 20000.0,
        'loss_std': 5000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Data Protection',
        'clause_type': 'confidentiality',
        'risk_score': 0.85,
        'breach_probability': 0.28,
        'loss_mean': 200000.0,
        'loss_std': 40000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Force Majeure',
        'clause_type': 'force majeure',
        'risk_score': 0.40,
        'breach_probability': 0.06,
        'loss_mean': 15000.0,
        'loss_std': 3000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Indemnification',
        'clause_type': 'indemnity',
        'risk_score': 0.90,
        'breach_probability': 0.30,
        'loss_mean': 250000.0,
        'loss_std': 50000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Renewal Terms',
        'clause_type': 'termination',
        'risk_score': 0.35,
        'breach_probability': 0.05,
        'loss_mean': 12000.0,
        'loss_std': 3000.0
    },
]

print("\n   Creating Contract 2: Master Services Agreement")
print(f"   Contract ID: {contract2_id}")
print(f"   Clauses: {len(contract2_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract2_id,
    clauses=contract2_clauses,
    jurisdiction='UK'
)
if success:
    print("   [OK] Contract 2 created successfully")
else:
    print("   [FAIL] Contract 2 creation failed")

# Sample Contract 3: Consulting Agreement
contract3_id = str(uuid.uuid4())
contract3_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Consulting Services',
        'clause_type': 'general',
        'risk_score': 0.25,
        'breach_probability': 0.04,
        'loss_mean': 8000.0,
        'loss_std': 2000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Hourly Rate Terms',
        'clause_type': 'payment',
        'risk_score': 0.50,
        'breach_probability': 0.10,
        'loss_mean': 30000.0,
        'loss_std': 8000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Non-Compete Clause',
        'clause_type': 'general',
        'risk_score': 0.65,
        'breach_probability': 0.16,
        'loss_mean': 50000.0,
        'loss_std': 12000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Work Product Ownership',
        'clause_type': 'intellectual property',
        'risk_score': 0.72,
        'breach_probability': 0.19,
        'loss_mean': 80000.0,
        'loss_std': 18000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Professional Liability',
        'clause_type': 'liability',
        'risk_score': 0.78,
        'breach_probability': 0.22,
        'loss_mean': 120000.0,
        'loss_std': 25000.0
    },
]

print("\n   Creating Contract 3: Consulting Agreement")
print(f"   Contract ID: {contract3_id}")
print(f"   Clauses: {len(contract3_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract3_id,
    clauses=contract3_clauses,
    jurisdiction='IN'
)
if success:
    print("   [OK] Contract 3 created successfully")
else:
    print("   [FAIL] Contract 3 creation failed")

# Sample Contract 4: Enterprise License Agreement
contract4_id = str(uuid.uuid4())
contract4_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'License Grant',
        'clause_type': 'general',
        'risk_score': 0.35,
        'breach_probability': 0.06,
        'loss_mean': 15000.0,
        'loss_std': 4000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Usage Restrictions',
        'clause_type': 'compliance',
        'risk_score': 0.68,
        'breach_probability': 0.17,
        'loss_mean': 65000.0,
        'loss_std': 15000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Subscription Fees',
        'clause_type': 'payment',
        'risk_score': 0.42,
        'breach_probability': 0.08,
        'loss_mean': 22000.0,
        'loss_std': 6000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'IP Infringement Indemnity',
        'clause_type': 'indemnity',
        'risk_score': 0.88,
        'breach_probability': 0.28,
        'loss_mean': 220000.0,
        'loss_std': 45000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Auto-Renewal Terms',
        'clause_type': 'termination',
        'risk_score': 0.48,
        'breach_probability': 0.09,
        'loss_mean': 18000.0,
        'loss_std': 5000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Service Warranties',
        'clause_type': 'warranty',
        'risk_score': 0.58,
        'breach_probability': 0.13,
        'loss_mean': 38000.0,
        'loss_std': 9000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Data Security',
        'clause_type': 'confidentiality',
        'risk_score': 0.82,
        'breach_probability': 0.24,
        'loss_mean': 180000.0,
        'loss_std': 35000.0
    },
]

print("\n   Creating Contract 4: Enterprise License Agreement")
print(f"   Contract ID: {contract4_id}")
print(f"   Clauses: {len(contract4_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract4_id,
    clauses=contract4_clauses,
    jurisdiction='SG'
)
if success:
    print("   [OK] Contract 4 created successfully")
else:
    print("   [FAIL] Contract 4 creation failed")

# Sample Contract 5: Vendor Services Agreement
contract5_id = str(uuid.uuid4())
contract5_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Delivery Milestones',
        'clause_type': 'general',
        'risk_score': 0.52,
        'breach_probability': 0.11,
        'loss_mean': 28000.0,
        'loss_std': 7000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Performance Standards',
        'clause_type': 'compliance',
        'risk_score': 0.62,
        'breach_probability': 0.15,
        'loss_mean': 45000.0,
        'loss_std': 11000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Progress Payments',
        'clause_type': 'payment',
        'risk_score': 0.55,
        'breach_probability': 0.12,
        'loss_mean': 35000.0,
        'loss_std': 9000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Quality Assurance',
        'clause_type': 'warranty',
        'risk_score': 0.67,
        'breach_probability': 0.17,
        'loss_mean': 55000.0,
        'loss_std': 13000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Penalty Clauses',
        'clause_type': 'liability',
        'risk_score': 0.73,
        'breach_probability': 0.20,
        'loss_mean': 95000.0,
        'loss_std': 22000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Termination Rights',
        'clause_type': 'termination',
        'risk_score': 0.60,
        'breach_probability': 0.14,
        'loss_mean': 42000.0,
        'loss_std': 10000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Confidential Information',
        'clause_type': 'confidentiality',
        'risk_score': 0.64,
        'breach_probability': 0.16,
        'loss_mean': 58000.0,
        'loss_std': 14000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Third-Party Claims',
        'clause_type': 'indemnity',
        'risk_score': 0.76,
        'breach_probability': 0.21,
        'loss_mean': 110000.0,
        'loss_std': 26000.0
    },
]

print("\n   Creating Contract 5: Vendor Services Agreement")
print(f"   Contract ID: {contract5_id}")
print(f"   Clauses: {len(contract5_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract5_id,
    clauses=contract5_clauses,
    jurisdiction='EU'
)
if success:
    print("   [OK] Contract 5 created successfully")
else:
    print("   [FAIL] Contract 5 creation failed")

# Sample Contract 6: Joint Venture Agreement
contract6_id = str(uuid.uuid4())
contract6_clauses = [
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Capital Contributions',
        'clause_type': 'payment',
        'risk_score': 0.71,
        'breach_probability': 0.18,
        'loss_mean': 75000.0,
        'loss_std': 17000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Profit Sharing',
        'clause_type': 'general',
        'risk_score': 0.59,
        'breach_probability': 0.14,
        'loss_mean': 48000.0,
        'loss_std': 12000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Management Control',
        'clause_type': 'general',
        'risk_score': 0.66,
        'breach_probability': 0.16,
        'loss_mean': 52000.0,
        'loss_std': 13000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'IP Ownership Rights',
        'clause_type': 'intellectual property',
        'risk_score': 0.84,
        'breach_probability': 0.26,
        'loss_mean': 190000.0,
        'loss_std': 38000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Exit Strategy',
        'clause_type': 'termination',
        'risk_score': 0.69,
        'breach_probability': 0.18,
        'loss_mean': 68000.0,
        'loss_std': 16000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Joint Liability',
        'clause_type': 'liability',
        'risk_score': 0.91,
        'breach_probability': 0.32,
        'loss_mean': 280000.0,
        'loss_std': 55000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Trade Secrets',
        'clause_type': 'confidentiality',
        'risk_score': 0.77,
        'breach_probability': 0.22,
        'loss_mean': 125000.0,
        'loss_std': 28000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Cross-Indemnification',
        'clause_type': 'indemnity',
        'risk_score': 0.86,
        'breach_probability': 0.27,
        'loss_mean': 210000.0,
        'loss_std': 42000.0
    },
    {
        'id': str(uuid.uuid4()),
        'clause_name': 'Regulatory Compliance',
        'clause_type': 'compliance',
        'risk_score': 0.74,
        'breach_probability': 0.20,
        'loss_mean': 88000.0,
        'loss_std': 20000.0
    },
]

print("\n   Creating Contract 6: Joint Venture Agreement")
print(f"   Contract ID: {contract6_id}")
print(f"   Clauses: {len(contract6_clauses)}")
success = schema.create_contract_with_risks(
    contract_id=contract6_id,
    clauses=contract6_clauses,
    jurisdiction='US-NY'
)
if success:
    print("   [OK] Contract 6 created successfully")
else:
    print("   [FAIL] Contract 6 creation failed")

# Verify the graph
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

with schema.driver.session() as session:
    # Count nodes
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
    """)

    print("\n[STATS] Node Counts:")
    total_nodes = 0
    for record in result:
        node_type = record['type']
        count = record['count']
        total_nodes += count
        print(f"   {node_type}: {count}")
    print(f"   ---")
    print(f"   TOTAL: {total_nodes}")

    # Count relationships
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
    """)

    print("\n[LINKS] Relationship Counts:")
    total_rels = 0
    for record in result:
        rel_type = record['rel_type']
        count = record['count']
        total_rels += count
        print(f"   {rel_type}: {count}")
    print(f"   ---")
    print(f"   TOTAL: {total_rels}")

print("\n" + "=" * 80)
print("[SUCCESS] SAMPLE GRAPH POPULATED SUCCESSFULLY!")
print("=" * 80)
print("\n[INFO] Test Contract IDs:")
print(f"   Contract 1 (Software Dev):      {contract1_id}")
print(f"   Contract 2 (MSA):               {contract2_id}")
print(f"   Contract 3 (Consulting):        {contract3_id}")
print(f"   Contract 4 (Enterprise License): {contract4_id}")
print(f"   Contract 5 (Vendor Services):   {contract5_id}")
print(f"   Contract 6 (Joint Venture):     {contract6_id}")
print("\n[WEB] View in Neo4j Browser:")
print("   http://localhost:7474")
print("\n[VIEW] View in Risk Intelligence Dashboard:")
print(f"   http://localhost:3000/risk-intelligence/{contract1_id}")
print("\n" + "=" * 80)
