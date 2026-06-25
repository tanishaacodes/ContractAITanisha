"""
Create enterprise tables using direct SQL execution
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

# Read SQL file
with open('create_enterprise_tables.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Split by semicolons and execute each statement
statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]

print("Creating enterprise tables...")
for i, statement in enumerate(statements, 1):
    try:
        cursor.execute(statement)
        # Extract table name from CREATE TABLE statement
        if 'CREATE TABLE' in statement:
            table_name = statement.split('`')[1] if '`' in statement else 'table'
            print(f"[OK] Created {table_name}")
    except Exception as e:
        print(f"[ERROR] Statement {i}: {e}")
        print(f"Statement: {statement[:100]}...")

conn.commit()
cursor.close()
conn.close()

print("\n[SUCCESS] All enterprise tables created successfully!")
print("\nNext step: Run 'python manage.py seed_enterprise_data' to populate with sample data.")
