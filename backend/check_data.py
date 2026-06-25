"""
Quick debug script to check database status
"""

import os
import django
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import Clause, ClauseVersion, ClauseEvent, ClauseHealthMetrics, Contract

print("=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

# Check contracts
contracts = Contract.objects.all()
print(f"\n📄 Contracts: {contracts.count()}")

# Check clauses
clauses = Clause.objects.all()
print(f"📋 Clauses: {clauses.count()}")
if clauses.exists():
    print(f"   First clause: {clauses.first().clause_name}")

# Check clause versions
versions = ClauseVersion.objects.all()
print(f"🔄 Clause Versions: {versions.count()}")

# Check clause events
events = ClauseEvent.objects.all()
print(f"📊 Clause Events: {events.count()}")

# Check health metrics
metrics = ClauseHealthMetrics.objects.all()
print(f"💚 Health Metrics: {metrics.count()}")

if metrics.exists():
    print("\n" + "=" * 60)
    print("HEALTH METRICS BREAKDOWN:")
    print("=" * 60)
    for m in metrics[:5]:
        print(f"  • {m.clause.clause_name[:40]}")
        print(f"    Health: {m.health_score:.2f} | Status: {m.status}")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)

if clauses.count() == 0:
    print("❌ No clauses found!")
    print("   → Upload some contracts first")
elif metrics.count() == 0:
    print("❌ No health metrics found!")
    print("   → Run: python populate_health_from_existing.py")
else:
    print("✅ Data looks good!")
    print("   → Check if backend is running on port 8002")
    print("   → Check browser console for API errors")
