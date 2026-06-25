from api.utils import parse_semantic_query
import json

queries = [
    # Risk-based
    'contract with high risk?',
    'show me high risk contracts',
    'low risk contracts',

    # Type-based
    'employment contracts',
    'find NDAs',

    # List all
    'show me uploaded contract',
    'list my contracts',
    'my contracts',
    'contracts?',

    # Combined
    'high risk employment contracts',
    'show me low risk NDAs',

    # Clause searches (should NOT trigger show_all)
    'show me termination clauses',
    'what are payment terms',
]

print("\n" + "="*80)
print("COMPREHENSIVE QUERY TESTING")
print("="*80 + "\n")

for query in queries:
    result = parse_semantic_query(query)
    filters = result['filters']

    filter_str = ', '.join([f'{k}={v}' for k, v in filters.items()])

    print(f"{query:45} -> {filter_str if filter_str else 'No filters'}")

print("\n" + "="*80 + "\n")
