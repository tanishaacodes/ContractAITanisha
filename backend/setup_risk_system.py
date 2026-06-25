"""
Risk System Setup Script
Initializes MySQL, Neo4j, and Qdrant for cross-contract risk analysis
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from risk.services import get_neo4j_service, get_qdrant_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_mysql():
    """Create MySQL tables for risk models"""
    logger.info("=" * 70)
    logger.info("STEP 1: Setting up MySQL database")
    logger.info("=" * 70)

    try:
        # Make migrations
        logger.info("Creating migrations for risk app...")
        call_command('makemigrations', 'risk')

        # Apply migrations
        logger.info("Applying migrations...")
        call_command('migrate')

        logger.info("✅ MySQL setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ MySQL setup failed: {e}")
        return False


def setup_neo4j():
    """Initialize Neo4j indexes and verify connection"""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: Setting up Neo4j Graph Database")
    logger.info("=" * 70)

    try:
        neo4j_service = get_neo4j_service()

        # Verify connection
        logger.info("Verifying Neo4j connection...")
        if not neo4j_service.verify_connection():
            raise Exception("Cannot connect to Neo4j. Please ensure Neo4j is running.")

        logger.info("✅ Neo4j connection verified")

        # Create indexes
        logger.info("Creating Neo4j indexes...")
        neo4j_service.create_indexes()

        logger.info("✅ Neo4j setup completed successfully")
        logger.info(f"   URI: {settings.NEO4J_URI}")
        logger.info(f"   User: {settings.NEO4J_USER}")

        return True

    except Exception as e:
        logger.error(f"❌ Neo4j setup failed: {e}")
        logger.error("   Please check:")
        logger.error("   1. Neo4j is installed and running")
        logger.error("   2. NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in settings.py")
        logger.error("   3. Neo4j is accessible at the configured URI")
        return False


def setup_qdrant():
    """Initialize Qdrant collection"""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3: Setting up Qdrant Vector Database")
    logger.info("=" * 70)

    try:
        logger.info("Initializing Qdrant service...")
        qdrant_service = get_qdrant_service()

        logger.info("✅ Qdrant setup completed successfully")
        logger.info(f"   Collection: {qdrant_service.COLLECTION_NAME}")
        logger.info(f"   Vector Size: {qdrant_service.VECTOR_SIZE}")
        logger.info(f"   URL: {settings.QDRANT_URL}")

        return True

    except Exception as e:
        logger.error(f"❌ Qdrant setup failed: {e}")
        logger.error("   Please check:")
        logger.error("   1. Qdrant is installed and running")
        logger.error("   2. QDRANT_URL in settings.py is correct")
        logger.error("   3. Qdrant is accessible at the configured URL")
        return False


def verify_dependencies():
    """Verify all required services are accessible"""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4: Verifying Dependencies")
    logger.info("=" * 70)

    issues = []

    # Check MySQL
    try:
        from django.db import connection
        connection.ensure_connection()
        logger.info("✅ MySQL connection verified")
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        issues.append("MySQL")

    # Check Ollama (for Qwen 7B)
    try:
        import requests
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Ollama connection verified")
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if settings.OLLAMA_MODEL in model_names:
                logger.info(f"   Model {settings.OLLAMA_MODEL} found")
            else:
                logger.warning(f"   ⚠️  Model {settings.OLLAMA_MODEL} not found")
                logger.warning(f"   Run: ollama pull {settings.OLLAMA_MODEL}")
        else:
            raise Exception("Ollama not responding")
    except Exception as e:
        logger.error(f"❌ Ollama connection failed: {e}")
        logger.error("   Please install Ollama and run: ollama pull qwen2.5:0.5b")
        issues.append("Ollama")

    return len(issues) == 0


def print_next_steps():
    """Print next steps for the user"""
    logger.info("\n" + "=" * 70)
    logger.info("🎉 SETUP COMPLETE!")
    logger.info("=" * 70)

    logger.info("\n📋 Next Steps:")
    logger.info("\n1. Start the Django backend:")
    logger.info("   cd django_backend")
    logger.info("   python manage.py runserver")

    logger.info("\n2. Start the React frontend:")
    logger.info("   cd frontend")
    logger.info("   npm start")

    logger.info("\n3. Navigate to: http://localhost:3000")

    logger.info("\n4. Go to 'Risk & Exposure' in the sidebar to:")
    logger.info("   - View portfolio risk overview")
    logger.info("   - See regional risk heatmap")
    logger.info("   - Analyze vendor exposure")
    logger.info("   - Detect cross-contract correlations")

    logger.info("\n📊 How to Analyze Contracts:")
    logger.info("   1. Upload contracts via 'Upload Contracts'")
    logger.info("   2. View contract details")
    logger.info("   3. Click 'Analyze Risk' button")
    logger.info("   4. Risk data will sync to Neo4j + Qdrant")
    logger.info("   5. View aggregated risks in 'Risk & Exposure' dashboard")

    logger.info("\n🔧 Configuration:")
    logger.info(f"   MySQL: {settings.DATABASES['default']['NAME']}")
    logger.info(f"   Neo4j: {settings.NEO4J_URI}")
    logger.info(f"   Qdrant: {settings.QDRANT_URL}")
    logger.info(f"   Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"   LLM Model: {settings.OLLAMA_MODEL}")

    logger.info("\n" + "=" * 70)


def main():
    """Main setup routine"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 10 + "Cross-Contract Risk & Exposure Setup" + " " * 22 + "║")
    logger.info("║" + " " * 15 + "ContractAI - Phase 2" + " " * 33 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    logger.info("\n")

    all_success = True

    # Step 1: MySQL
    if not setup_mysql():
        all_success = False

    # Step 2: Neo4j
    if not setup_neo4j():
        all_success = False

    # Step 3: Qdrant
    if not setup_qdrant():
        all_success = False

    # Step 4: Verify dependencies
    if not verify_dependencies():
        all_success = False

    # Print results
    if all_success:
        print_next_steps()
    else:
        logger.error("\n" + "=" * 70)
        logger.error("⚠️  SETUP COMPLETED WITH WARNINGS")
        logger.error("=" * 70)
        logger.error("\nSome components failed to initialize.")
        logger.error("Please resolve the issues above and run this script again.")
        logger.error("\n" + "=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
