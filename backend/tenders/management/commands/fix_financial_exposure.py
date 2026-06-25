"""
Management command to fix incorrect financial exposure values
Usage: python manage.py fix_financial_exposure
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from tenders.models import BidActionItem, Tender
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fixes incorrect financial exposure values in bid action items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tender-id',
            type=str,
            help='Fix only specific tender ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tender_id = options.get('tender_id')

        if tender_id:
            tenders = Tender.objects.filter(id=tender_id)
        else:
            tenders = Tender.objects.all()

        fixed_count = 0
        total_actions = 0

        for tender in tenders:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Checking tender: {tender.title}")
            self.stdout.write(f"Tender value: Rs.{float(tender.estimated_value or 0) / 10000000:.2f} Cr")

            actions = BidActionItem.objects.filter(tender=tender)
            total_actions += actions.count()

            if not actions.exists():
                self.stdout.write(self.style.WARNING("  No action items found"))
                continue

            # Calculate current total exposure
            current_exposure = actions.aggregate(
                Sum('financial_exposure')
            )['financial_exposure__sum'] or 0

            self.stdout.write(f"Current total exposure: Rs.{float(current_exposure) / 10000000:.2f} Cr")

            tender_value = float(tender.estimated_value or 0)
            max_item_cost = tender_value * 0.3 if tender_value > 0 else 1000000000

            for action in actions:
                old_exposure = float(action.financial_exposure)

                # Check if exposure is unreasonable
                if old_exposure > max_item_cost or old_exposure > 1000000000:
                    # Cap it
                    new_exposure = min(old_exposure, max_item_cost, 1000000000)

                    self.stdout.write(
                        self.style.WARNING(
                            f"  - {action.title[:50]}: "
                            f"Rs.{old_exposure/10000000:.2f} Cr -> "
                            f"Rs.{new_exposure/10000000:.2f} Cr"
                        )
                    )

                    if not dry_run:
                        action.financial_exposure = Decimal(str(new_exposure))
                        action.save(update_fields=['financial_exposure'])

                    fixed_count += 1

            # Recalculate after fixes
            if not dry_run and fixed_count > 0:
                new_exposure = actions.aggregate(
                    Sum('financial_exposure')
                )['financial_exposure__sum'] or 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"New total exposure: Rs.{float(new_exposure) / 10000000:.2f} Cr"
                    )
                )

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal actions checked: {total_actions}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Actions {'would be ' if dry_run else ''}fixed: {fixed_count}"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a dry run. Use without --dry-run to apply changes."
                )
            )
