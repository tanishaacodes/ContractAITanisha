"""
Migration script to assign Professional Plan to all existing users.
This is a one-time script to grandfather existing users into the Professional Plan.
"""
import os
import django
import sys

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from core.models import User, PricingPlan

def assign_professional_plan():
    """Assign Professional Plan to all existing users without a plan"""

    try:
        # Get Professional Plan
        professional_plan = PricingPlan.objects.get(plan_type='PROFESSIONAL')
        print(f"Found Professional Plan: {professional_plan.display_name}")

        # Get all users without a plan
        users_without_plan = User.objects.filter(current_plan__isnull=True)
        count = users_without_plan.count()

        if count == 0:
            print("No users found without a plan. All users are already assigned to a plan.")
            return

        print(f"\nFound {count} users without a plan. Assigning Professional Plan...")

        # Assign Professional Plan to all users
        updated_count = users_without_plan.update(current_plan=professional_plan)

        print(f"\nSuccessfully assigned Professional Plan to {updated_count} users!")

        # Print summary
        print("\n" + "="*60)
        print("SUMMARY: Users by Plan")
        print("="*60)

        for plan in PricingPlan.objects.all():
            user_count = User.objects.filter(current_plan=plan).count()
            print(f"{plan.display_name:25} | {user_count} users")

        unassigned_count = User.objects.filter(current_plan__isnull=True).count()
        print(f"{'No Plan Assigned':25} | {unassigned_count} users")
        print("="*60)

    except PricingPlan.DoesNotExist:
        print("ERROR: Professional Plan not found in database.")
        print("Please run 'python seed_pricing_plans.py' first to create pricing plans.")
        sys.exit(1)

if __name__ == '__main__':
    assign_professional_plan()
