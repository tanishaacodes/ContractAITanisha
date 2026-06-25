from api.utils import parse_semantic_query
import json

queries = [
    'show me uploaded contract',
    'list my contracts',
    'show all contracts',
    'display my contracts',
    'what contracts do I have',
    'get all contracts'
]

print("\nTesting 'show all' filter detection:\n")
for q in queries:
    result = parse_semantic_query(q)
    has_show_all = 'show_all' in result['filters']
    print(f"{q:35} -> show_all: {has_show_all}")
