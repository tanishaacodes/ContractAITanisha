import re

# Read SQL file
with open(r'C:\Users\Chiku\Downloads\contractai_backup (14).sql', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all INSERT statements
inserts = re.findall(r'INSERT INTO `([^`]+)` VALUES', content)

# Count by table
from collections import Counter
table_counts = Counter(inserts)

print("Tables with data in backup:")
print("-" * 50)
for table, count in sorted(table_counts.items()):
    print(f"{table:40} {count:>6} rows")

print(f"\nTotal tables with data: {len(table_counts)}")
print(f"Total rows: {sum(table_counts.values())}")
