"""
Drop enterprise tables to allow clean migration
"""
import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn = MySQLdb.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    passwd=os.getenv('DB_PASSWORD', ''),
    db=os.getenv('DB_NAME', 'contractai')
)

cursor = conn.cursor()

# Drop tables in correct order (respect foreign keys)
tables = [
    'enterprise_contract_commodities',
    'enterprise_contract_suppliers',
    'enterprise_monte_carlo_simulations',
    'enterprise_commodities',
    'enterprise_suppliers',
    'enterprise_geopolitical_risks',
]

print("Dropping enterprise tables...")
for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"[OK] Dropped {table}")
    except Exception as e:
        print(f"[ERROR] Error dropping {table}: {e}")

conn.commit()
cursor.close()
conn.close()

print("\n[SUCCESS] All enterprise tables dropped. You can now run migrations.")
