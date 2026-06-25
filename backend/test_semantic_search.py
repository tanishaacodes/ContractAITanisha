#!/usr/bin/env python3
"""
Test script for semantic query parsing functionality
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
import django
django.setup()

from api.utils import parse_semantic_query

def test_query(query):
    """Test a single query and print results"""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    result = parse_semantic_query(query)

    print(f"\nFilters detected:")
    for key, value in result['filters'].items():
        print(f"  - {key}: {value}")

    print(f"\nSearch terms: {result['search_terms']}")
    print(f"Semantic query: {result['semantic_query']}")

if __name__ == '__main__':
    # Test various queries
    test_queries = [
        "Show me low risk contracts",
        "Find all high risk employment contracts",
        "Contracts with arbitration in Dubai",
        "What are the payment terms in my NDA?",
        "Show me approved consulting contracts",
        "Find contracts with high liability",
        "Which contracts have termination clauses?",
        "Medium risk contracts in USA jurisdiction",
    ]

    for query in test_queries:
        test_query(query)

    print(f"\n{'='*70}")
    print("Test complete!")
    print(f"{'='*70}\n")
