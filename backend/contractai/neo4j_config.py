"""
Neo4j Configuration
====================
Configuration and connection management for Neo4j graph database.
"""

import os
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class Neo4jConfig:
    """Neo4j database configuration"""

    # Get from environment or use defaults
    URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    USERNAME = os.getenv('NEO4J_USERNAME') or os.getenv('NEO4J_USER', 'neo4j')  # Support both
    PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')  # Match settings.py default
    DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

    # Connection settings
    MAX_CONNECTION_LIFETIME = 3600  # 1 hour
    MAX_CONNECTION_POOL_SIZE = 50
    CONNECTION_ACQUISITION_TIMEOUT = 60  # seconds

    @classmethod
    def get_connection_params(cls):
        """Get connection parameters as dict"""
        return {
            'uri': cls.URI,
            'auth': (cls.USERNAME, cls.PASSWORD),
            'max_connection_lifetime': cls.MAX_CONNECTION_LIFETIME,
            'max_connection_pool_size': cls.MAX_CONNECTION_POOL_SIZE,
            'connection_acquisition_timeout': cls.CONNECTION_ACQUISITION_TIMEOUT
        }


class Neo4jConnection:
    """
    Singleton Neo4j connection manager.
    Provides thread-safe access to Neo4j driver.
    """

    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Don't connect on init - defer until first use
        pass

    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            config = Neo4jConfig.get_connection_params()
            self._driver = GraphDatabase.driver(
                config['uri'],
                auth=config['auth'],
                max_connection_lifetime=config['max_connection_lifetime'],
                max_connection_pool_size=config['max_connection_pool_size'],
                connection_acquisition_timeout=config['connection_acquisition_timeout']
            )

            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info(f"[NEO4J] Connected to {config['uri']}")

        except Exception as e:
            logger.error(f"[NEO4J] Failed to connect: {e}")
            self._driver = None
            # Don't raise - just log and continue without Neo4j

    def get_driver(self):
        """Get Neo4j driver instance"""
        if self._driver is None:
            try:
                self._connect()
            except Exception:
                pass  # Connection failed, return None
        return self._driver

    def close(self):
        """Close Neo4j connection"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("[NEO4J] Connection closed")

    def is_connected(self):
        """Check if connected to Neo4j"""
        if self._driver is None:
            return False
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False


# Global connection instance
neo4j_connection = Neo4jConnection()


def get_neo4j_driver():
    """Get Neo4j driver - convenience function"""
    return neo4j_connection.get_driver()


def check_neo4j_available():
    """Check if Neo4j is available — triggers connection attempt if not yet connected."""
    try:
        driver = neo4j_connection.get_driver()  # establishes connection if _driver is None
        return driver is not None and neo4j_connection.is_connected()
    except Exception:
        return False
