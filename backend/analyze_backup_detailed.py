import re

# Read SQL file
with open(r'C:\Users\Chiku\Downloads\contractai_backup (14).sql', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all INSERT statements with their data
pattern = r"INSERT INTO `([^`]+)` VALUES\s+(.*?);"
matches = re.findall(pattern, content, re.DOTALL)

print("Tables with data in backup:")
print("-" * 80)
for table, values in matches:
    # Count rows by counting commas at the start of value groups
    # Each row starts with ( and rows are separated by ),(
    row_count = values.count('),(') + 1 if values.strip() else 0

    # Get first 100 chars of data
    preview = values[:100].replace('\n', ' ')

    print(f"{table:40} {row_count:>6} rows  |  {preview}...")

print(f"\nTotal tables with data: {len(matches)}")
