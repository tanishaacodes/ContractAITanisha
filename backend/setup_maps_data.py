"""
Setup Contract Intelligence Maps Data
Adds required columns and populates test data
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.db import connection

def run():
    with connection.cursor() as cursor:
        # Step 1: Check if columns exist and add them if needed
        print("Step 1: Adding required columns to contracts table...")

        # Try adding columns one by one
        columns = [
            ("business_unit", "VARCHAR(100)"),
            ("version", "INT DEFAULT 1"),
            ("version_date", "DATETIME"),
            ("total_liability", "DECIMAL(18,2) DEFAULT 0")
        ]

        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}")
                print(f"  [+] Added {col_name}")
            except Exception as e2:
                if "Duplicate column" in str(e2):
                    print(f"  [OK] Column {col_name} already exists")
                else:
                    print(f"  [!] {col_name}: {e2}")

        # Step 2: Count contracts needing update
        cursor.execute("""
            SELECT COUNT(*)
            FROM contracts
            WHERE business_unit IS NULL OR business_unit = ''
               OR total_liability IS NULL OR total_liability = 0
        """)
        count = cursor.fetchone()[0]
        print(f"\nStep 2: Found {count} contracts to update")

        if count == 0:
            print("[OK] All contracts already have required data!")
            cursor.execute("SELECT COUNT(*) FROM contracts WHERE business_unit IS NOT NULL")
            total = cursor.fetchone()[0]
            print(f"Total contracts with business units: {total}")
            return

        # Step 3: Get contract IDs that need updating
        cursor.execute("""
            SELECT id
            FROM contracts
            WHERE business_unit IS NULL OR business_unit = ''
               OR total_liability IS NULL OR total_liability = 0
        """)
        contract_ids = [row[0] for row in cursor.fetchall()]

        # Step 4: Update contracts with business units and liability
        print(f"\nStep 3: Updating {len(contract_ids)} contracts...")
        business_units = ['EPC', 'Oil & Gas', 'Defense', 'IT Services', 'Manufacturing']

        updated = 0
        for idx, contract_id in enumerate(contract_ids):
            bu = business_units[idx % len(business_units)]
            total_liability = random.uniform(100000, 2100000)
            contract_value = str(int(random.uniform(500000, 5500000)))

            cursor.execute("""
                UPDATE contracts
                SET business_unit = %s,
                    version = 1,
                    total_liability = %s,
                    contractValue = CASE
                        WHEN contractValue IS NULL OR contractValue = ''
                        THEN %s
                        ELSE contractValue
                    END
                WHERE id = %s
            """, [bu, total_liability, contract_value, contract_id])

            updated += 1
            if updated % 20 == 0:
                print(f"  Updated {updated}/{len(contract_ids)} contracts...")

        print(f"[OK] Updated {updated} contracts!")

        # Step 5: Show summary
        print("\nStep 4: Business Unit Summary:")
        for bu in business_units:
            cursor.execute("""
                SELECT COUNT(*), AVG(total_liability)
                FROM contracts
                WHERE business_unit = %s
            """, [bu])
            count, avg_liability = cursor.fetchone()
            avg_str = f"${avg_liability:,.2f}" if avg_liability else "N/A"
            print(f"  {bu}: {count} contracts, Avg Liability: {avg_str}")

        # Show sample data
        print("\nStep 5: Sample contracts:")
        cursor.execute("""
            SELECT id, filename, business_unit, version, contractValue, total_liability
            FROM contracts
            WHERE business_unit IS NOT NULL
            LIMIT 5
        """)
        for row in cursor.fetchall():
            contract_id, filename, bu, version, value, liability = row
            print(f"  {bu:15} | v{version} | Value: ${value:>10} | Liability: ${liability:>12,.2f}")

        print("\n==> Data is ready! Refresh your browser at http://localhost:5173/contract-maps")

if __name__ == '__main__':
    run()
