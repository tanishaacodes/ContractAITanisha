"""
Initialize Qdrant with silent risk patterns
Based on exact ContractAI specifications
"""
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from ai.embedding import embed_clause_pair
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

print("=" * 60)
print("SILENT RISK PATTERNS - QDRANT INITIALIZATION")
print("=" * 60)

# Initialize Qdrant client
client = QdrantClient("localhost", port=6333)

COLLECTION = "silent_risk_patterns"

# Check if collection exists, delete and recreate
try:
    client.delete_collection(COLLECTION)
    print(f"[OK] Deleted existing collection: {COLLECTION}")
except Exception:
    pass

# Create collection
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)
print(f"[OK] Created collection: {COLLECTION}")

# Define known dangerous clause-pair patterns
risk_patterns = [
    {
        "clause_a": "The licensee shall retain all intellectual property rights in any modifications or derivative works.",
        "clause_b": "Upon termination, all rights revert to the licensor.",
        "risk_type": "CROSS_CLAUSE_CONFLICT",
        "pattern": "ip_ownership_termination_conflict",
        "impact_multiplier": 0.5
    },
    {
        "clause_a": "Payment terms: Net 30 days from invoice date.",
        "clause_b": "Either party may terminate for convenience with 30 days notice.",
        "risk_type": "TERMINATION_PAYMENT_MISMATCH",
        "pattern": "termination_without_proration",
        "impact_multiplier": 0.45
    },
    {
        "clause_a": "This agreement shall automatically renew for successive one-year terms.",
        "clause_b": "Fees may increase by up to 10% annually upon renewal.",
        "risk_type": "HIDDEN_COST_ESCALATION",
        "pattern": "auto_renewal_price_escalation",
        "impact_multiplier": 0.6
    },
    {
        "clause_a": "The indemnifying party shall defend, indemnify, and hold harmless the other party from any claims.",
        "clause_b": "The obligations under this agreement shall survive termination for a period of 5 years.",
        "risk_type": "LONG_TAIL_LIABILITY",
        "pattern": "indemnity_survival_extension",
        "impact_multiplier": 0.7
    },
    {
        "clause_a": "All confidential information shall remain the property of the disclosing party.",
        "clause_b": "The receiving party may use confidential information for any purpose related to the business relationship.",
        "risk_type": "DATA_EXPOSURE_RISK",
        "pattern": "confidentiality_broad_use",
        "impact_multiplier": 0.4
    },
    {
        "clause_a": "Liability shall be limited to the fees paid in the 12 months preceding the claim.",
        "clause_b": "The foregoing limitation shall not apply to breaches of confidentiality, IP infringement, or gross negligence.",
        "risk_type": "UNCAPPED_LIABILITY",
        "pattern": "liability_cap_exceptions",
        "impact_multiplier": 0.65
    },
    {
        "clause_a": "This agreement may only be terminated for material breach.",
        "clause_b": "Upon termination, customer shall immediately pay all outstanding fees for the remainder of the term.",
        "risk_type": "NON_RECOVERABLE_SPEND",
        "pattern": "termination_full_payment",
        "impact_multiplier": 0.5
    },
    {
        "clause_a": "Customer data shall be retained for 90 days after termination.",
        "clause_b": "Provider may use customer data for analytics and service improvement.",
        "risk_type": "DATA_RETENTION_RISK",
        "pattern": "data_retention_broad_use",
        "impact_multiplier": 0.35
    },
    {
        "clause_a": "Changes to service terms may be made at any time with 30 days notice.",
        "clause_b": "Continued use of the service constitutes acceptance of modified terms.",
        "risk_type": "UNILATERAL_MODIFICATION",
        "pattern": "forced_acceptance_changes",
        "impact_multiplier": 0.4
    },
    {
        "clause_a": "Provider makes no warranties, express or implied, regarding service availability.",
        "clause_b": "Customer is solely responsible for backup and disaster recovery.",
        "risk_type": "LATENT_FINANCIAL_TRIGGER",
        "pattern": "no_warranty_no_backup",
        "impact_multiplier": 0.55
    },
    {
        "clause_a": "This agreement shall be governed by the laws of Delaware.",
        "clause_b": "Disputes shall be resolved through binding arbitration in New York.",
        "risk_type": "JURISDICTION_CONFLICT",
        "pattern": "governing_law_venue_mismatch",
        "impact_multiplier": 0.3
    },
    {
        "clause_a": "Service credits are the sole remedy for any service level failures.",
        "clause_b": "Maximum service credits shall not exceed 10% of monthly fees.",
        "risk_type": "REMEDIES_LIMITATION",
        "pattern": "capped_service_credits",
        "impact_multiplier": 0.4
    }
]

print(f"\nPopulating {len(risk_patterns)} risk patterns...")

points = []
for idx, pattern in enumerate(risk_patterns):
    # Generate clause-pair embedding
    vector = embed_clause_pair(pattern["clause_a"], pattern["clause_b"])

    # Create point with metadata
    point = PointStruct(
        id=idx,
        vector=vector,
        payload={
            "risk_type": pattern["risk_type"],
            "pattern": pattern["pattern"],
            "impact_multiplier": pattern["impact_multiplier"],
            "clause_pair": [pattern["clause_a"][:100], pattern["clause_b"][:100]]
        }
    )
    points.append(point)
    print(f"  [OK] {pattern['risk_type']}")

# Batch upsert
client.upsert(
    collection_name=COLLECTION,
    points=points
)

print(f"\n[OK] Successfully populated {len(risk_patterns)} risk patterns in Qdrant")

# Verify
collection_info = client.get_collection(COLLECTION)
print(f"[OK] Collection '{COLLECTION}' now has {collection_info.points_count} points")

print("\n" + "=" * 60)
print("SILENT RISK PATTERNS INITIALIZATION COMPLETE")
print("=" * 60)
