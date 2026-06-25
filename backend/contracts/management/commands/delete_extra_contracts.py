from django.core.management.base import BaseCommand
from contracts.models import Contract

class Command(BaseCommand):
    help = 'Delete all contracts except the 5 main ones'

    def handle(self, *args, **kwargs):
        # Contracts to keep
        KEEP_KEYWORDS = [
            'High_Risk_Constructi',
            'SOFTWARE DEVELO',
            'MANUFACTURING',
            'EXCLUSIVE DISTRIBU',
            'COMMERCIAL LEASE'
        ]

        all_contracts = Contract.objects.all()
        self.stdout.write(f"\n📊 Total contracts: {all_contracts.count()}")

        # Separate contracts
        to_keep = []
        to_delete = []

        for contract in all_contracts:
            name = contract.filename or contract.title or str(contract.id)
            should_keep = any(kw in name for kw in KEEP_KEYWORDS)

            if should_keep:
                to_keep.append((contract.id, name))
            else:
                to_delete.append((contract.id, name))

        self.stdout.write(f"\n✅ Keeping {len(to_keep)} contracts:")
        for cid, name in to_keep:
            self.stdout.write(f"  ✓ {name}")

        self.stdout.write(f"\n🗑️  Deleting {len(to_delete)} contracts:")
        for cid, name in to_delete:
            self.stdout.write(f"  ✗ {name}")

        if not to_delete:
            self.stdout.write(self.style.SUCCESS("\n✅ No contracts to delete!"))
            return

        # Delete contracts
        self.stdout.write(f"\n⚠️  Deleting {len(to_delete)} contracts...")

        deleted_ids = [cid for cid, _ in to_delete]
        deleted_count = Contract.objects.filter(id__in=deleted_ids).delete()[0]

        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully deleted {deleted_count} contracts!"))
        self.stdout.write(self.style.SUCCESS(f"📌 Remaining: {Contract.objects.count()} contracts"))
