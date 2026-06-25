import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from neo4j import GraphDatabase
from django.conf import settings

try:
    print("[INFO] Connecting to Neo4j...")
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        result = session.run('MATCH (n) DETACH DELETE n RETURN count(n) as deleted')
        record = result.single()
        deleted = record['deleted'] if record else 0
        print(f'[SUCCESS] Deleted {deleted} nodes and their relationships from Neo4j')
        
    driver.close()
    print('[COMPLETE] Neo4j graph database has been cleared!')
    
except Exception as e:
    print(f'[ERROR] Failed to clear Neo4j: {str(e)}')
    import traceback
    traceback.print_exc()
