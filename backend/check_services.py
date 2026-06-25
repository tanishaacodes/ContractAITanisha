#!/usr/bin/env python3
"""
Service Health Check Script
Verifies Neo4j and Ollama are running and accessible
"""

import requests
from neo4j import GraphDatabase
import sys

def check_neo4j():
    """Check Neo4j connection"""
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password123")
        )
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("[OK] Neo4j: Connected (bolt://localhost:7687)")
                return True
        driver.close()
    except Exception as e:
        print(f"[FAIL] Neo4j: Not running or not accessible")
        print(f"       Error: {str(e)}")
        print(f"       Install from: https://neo4j.com/download/")
        return False

def check_ollama():
    """Check Ollama service"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"[OK] Ollama: Running (http://localhost:11434)")
            if models:
                print(f"     Models installed: {', '.join([m['name'] for m in models])}")
            else:
                print(f"     [WARN] No models installed. Run: ollama pull qwen2.5:0.5b")
            return True
    except Exception as e:
        print(f"[FAIL] Ollama: Not running or not accessible")
        print(f"       Error: {str(e)}")
        print(f"       Install from: https://ollama.ai/download")
        return False

def main():
    print("\n=== Checking Arbitration Services ===\n")

    neo4j_ok = check_neo4j()
    ollama_ok = check_ollama()

    print("\n" + "="*50)
    if neo4j_ok and ollama_ok:
        print("[SUCCESS] All services are running!")
        print("\nYou can now use full arbitration features:")
        print("  - enable_neo4j=True")
        print("  - enable_clause_rewrite=True")
        sys.exit(0)
    else:
        print("[WARN] Some services are not running")
        print("\nCore features still work without these services:")
        print("  - Clause extraction")
        print("  - Risk scoring (8 dimensions)")
        print("  - Monte Carlo simulation")
        print("  - Tribunal simulation")
        print("  - LegalBERT embeddings")
        print("  - Database persistence")
        sys.exit(1)

if __name__ == "__main__":
    main()
