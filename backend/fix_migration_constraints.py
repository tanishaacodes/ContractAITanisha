import re

# Read the migration file
with open('core/migrations/0046_add_negotiation_models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ForeignKey( with ForeignKey(db_constraint=False,
# But only if db_constraint is not already present
def add_db_constraint(match):
    fk_content = match.group(0)
    if 'db_constraint' in fk_content:
        return fk_content
    return fk_content.replace('models.ForeignKey(', 'models.ForeignKey(db_constraint=False, ')

content = re.sub(r'models\.ForeignKey\([^)]+\)', add_db_constraint, content)

# Write back
with open('core/migrations/0046_add_negotiation_models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all ForeignKey fields to include db_constraint=False")
