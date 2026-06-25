"""
Kafka Event Streaming Pipeline
================================
Integrates with Docker Kafka for real-time legal event processing.

Producers:
- Legal crawler → Kafka topics
- Risk assessments → Kafka topics
- Contract analysis events

Consumers:
- Event processing pipeline
- Real-time dashboard updates
- Simulation triggers
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Try Kafka import
try:
    from kafka import KafkaProducer, KafkaConsumer, TopicPartition
    from kafka.errors import KafkaError, NoBrokersAvailable
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("kafka-python not installed. Run: pip install kafka-python")
    KAFKA_AVAILABLE = False

# Import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("redis not installed. Run: pip install redis")
    REDIS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# KAFKA CONFIGURATION
# ═══════════════════════════════════════════════════════════════

KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],  # Docker: kafka:9092
    'client_id': 'primecontract-legal-ai',
    'compression_type': 'gzip',
    'max_request_size': 1048576,  # 1MB
}

# Kafka Topics
TOPICS = {
    'LEGAL_EVENTS': 'legal-events',
    'RISK_ASSESSMENTS': 'risk-assessments',
    'CONTRACT_ANALYSIS': 'contract-analysis',
    'CASE_LAW_UPDATES': 'caselaw-updates',
    'SIMULATION_TRIGGERS': 'simulation-triggers',
    'ALERTS': 'legal-alerts',
}


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class KafkaEvent:
    """Base event structure for Kafka messages."""
    event_id: str
    event_type: str
    timestamp: str
    source: str
    data: Dict[str, Any]
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    metadata: Optional[Dict] = None

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'KafkaEvent':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
# KAFKA PRODUCER
# ═══════════════════════════════════════════════════════════════

class LegalEventProducer:
    """
    Kafka producer for legal events.
    Publishes events from crawler, risk assessments, etc.
    """

    def __init__(self, bootstrap_servers: Optional[List[str]] = None):
        """Initialize Kafka producer."""
        self.bootstrap_servers = bootstrap_servers or KAFKA_CONFIG['bootstrap_servers']
        self.producer = None
        self.enabled = False

        if KAFKA_AVAILABLE:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    compression_type=KAFKA_CONFIG['compression_type'],
                    max_request_size=KAFKA_CONFIG['max_request_size'],
                    acks='all',  # Wait for all replicas
                    retries=3,
                )
                self.enabled = True
                logger.info(f"Kafka producer connected to {self.bootstrap_servers}")
            except NoBrokersAvailable:
                logger.warning("Kafka brokers not available. Running in fallback mode.")
            except Exception as e:
                logger.error(f"Error initializing Kafka producer: {e}")

    def publish_legal_event(self, event: Dict[str, Any], topic: str = None) -> bool:
        """
        Publish legal event to Kafka.

        Args:
            event: Event data dictionary
            topic: Kafka topic (defaults to LEGAL_EVENTS)

        Returns:
            True if published successfully
        """
        if not self.enabled or self.producer is None:
            logger.debug("Kafka not enabled, skipping publish")
            return False

        topic = topic or TOPICS['LEGAL_EVENTS']

        try:
            # Create Kafka event
            kafka_event = KafkaEvent(
                event_id=event.get('event_id', f"evt_{int(time.time())}"),
                event_type=event.get('event_type', 'unknown'),
                timestamp=event.get('timestamp', datetime.now().isoformat()),
                source=event.get('source', 'system'),
                data=event,
                priority=event.get('risk_level', 'MEDIUM')
            )

            # Publish
            future = self.producer.send(
                topic,
                key=kafka_event.event_id,
                value=kafka_event.to_json()
            )

            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=5)

            logger.info(
                f"Published event {kafka_event.event_id} to {topic} "
                f"[partition={record_metadata.partition}, offset={record_metadata.offset}]"
            )
            return True

        except KafkaError as e:
            logger.error(f"Kafka error publishing event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False

    def publish_risk_assessment(self, contract_id: str, risk_data: Dict) -> bool:
        """Publish risk assessment result."""
        event = {
            'event_id': f"risk_{contract_id}_{int(time.time())}",
            'event_type': 'risk_assessment',
            'contract_id': contract_id,
            'timestamp': datetime.now().isoformat(),
            'source': 'bayesian_engine',
            'risk_level': risk_data.get('legal_risk_level', 'MEDIUM'),
            'data': risk_data
        }
        return self.publish_legal_event(event, TOPICS['RISK_ASSESSMENTS'])

    def publish_case_update(self, case_data: Dict) -> bool:
        """Publish case law update."""
        event = {
            'event_id': f"case_{case_data.get('case_id', int(time.time()))}",
            'event_type': 'case_law_update',
            'timestamp': datetime.now().isoformat(),
            'source': 'case_crawler',
            'data': case_data
        }
        return self.publish_legal_event(event, TOPICS['CASE_LAW_UPDATES'])

    def publish_alert(self, alert_type: str, message: str, severity: str = "MEDIUM") -> bool:
        """Publish legal alert."""
        event = {
            'event_id': f"alert_{int(time.time())}",
            'event_type': 'alert',
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'source': 'alert_system'
        }
        return self.publish_legal_event(event, TOPICS['ALERTS'])

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


# ═══════════════════════════════════════════════════════════════
# KAFKA CONSUMER
# ═══════════════════════════════════════════════════════════════

class LegalEventConsumer:
    """
    Kafka consumer for legal events.
    Processes events and triggers actions.
    """

    def __init__(
        self,
        topics: List[str],
        group_id: str = 'legal-processor',
        bootstrap_servers: Optional[List[str]] = None
    ):
        """Initialize Kafka consumer."""
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or KAFKA_CONFIG['bootstrap_servers']
        self.consumer = None
        self.enabled = False
        self.handlers = {}

        if KAFKA_AVAILABLE:
            try:
                self.consumer = KafkaConsumer(
                    *topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    max_poll_records=100,
                    consumer_timeout_ms=1000,
                )
                self.enabled = True
                logger.info(f"Kafka consumer subscribed to {topics}")
            except NoBrokersAvailable:
                logger.warning("Kafka brokers not available. Consumer disabled.")
            except Exception as e:
                logger.error(f"Error initializing Kafka consumer: {e}")

    def register_handler(self, event_type: str, handler_func):
        """
        Register event handler function.

        Args:
            event_type: Type of event to handle
            handler_func: Function(event_data) to call
        """
        self.handlers[event_type] = handler_func
        logger.info(f"Registered handler for {event_type}")

    def consume_events(self, max_events: Optional[int] = None):
        """
        Consume and process events.

        Args:
            max_events: Maximum number of events to process (None = infinite)
        """
        if not self.enabled or self.consumer is None:
            logger.warning("Kafka consumer not enabled")
            return

        processed = 0
        logger.info("Starting event consumption...")

        try:
            for message in self.consumer:
                try:
                    # Parse event
                    event_data = message.value
                    event_type = event_data.get('event_type', 'unknown')

                    logger.debug(
                        f"Received event: {event_type} from {message.topic} "
                        f"[partition={message.partition}, offset={message.offset}]"
                    )

                    # Call handler if registered
                    handler = self.handlers.get(event_type)
                    if handler:
                        handler(event_data)
                    else:
                        self._default_handler(event_data)

                    processed += 1

                    # Stop if max_events reached
                    if max_events and processed >= max_events:
                        logger.info(f"Processed {processed} events, stopping")
                        break

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            logger.info(f"Consumed {processed} events")

    def _default_handler(self, event_data: Dict):
        """Default event handler."""
        logger.info(f"No handler for event type: {event_data.get('event_type')}")

    def close(self):
        """Close consumer connection."""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")


# ═══════════════════════════════════════════════════════════════
# REDIS CACHE INTEGRATION
# ═══════════════════════════════════════════════════════════════

class RedisCache:
    """
    Redis cache for legal data.
    Caches embeddings, risk scores, case law results.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """Initialize Redis connection."""
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self.enabled = False

        if REDIS_AVAILABLE:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.client.ping()
                self.enabled = True
                logger.info(f"Redis connected to {host}:{port}")
            except redis.ConnectionError:
                logger.warning("Redis not available. Running without cache.")
            except Exception as e:
                logger.error(f"Error connecting to Redis: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or self.client is None:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        if not self.enabled or self.client is None:
            return False

        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str):
        """Delete key from cache."""
        if self.enabled and self.client:
            try:
                self.client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

    def cache_embedding(self, text: str, embedding: List[float], ttl: int = 86400):
        """Cache embedding vector (24 hour TTL)."""
        key = f"embedding:{hash(text)}"
        return self.set(key, embedding, ttl)

    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = f"embedding:{hash(text)}"
        return self.get(key)

    def cache_risk_score(self, contract_id: str, risk_data: Dict, ttl: int = 3600):
        """Cache risk assessment (1 hour TTL)."""
        key = f"risk:{contract_id}"
        return self.set(key, risk_data, ttl)

    def get_cached_risk_score(self, contract_id: str) -> Optional[Dict]:
        """Get cached risk assessment."""
        key = f"risk:{contract_id}"
        return self.get(key)

    def cache_search_results(self, query: str, results: List[Dict], ttl: int = 1800):
        """Cache search results (30 min TTL)."""
        key = f"search:{hash(query)}"
        return self.set(key, results, ttl)

    def get_cached_search_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results."""
        key = f"search:{hash(query)}"
        return self.get(key)

    def flush_all(self):
        """Flush all cache (use with caution)."""
        if self.enabled and self.client:
            self.client.flushdb()
            logger.warning("Redis cache flushed")


# ═══════════════════════════════════════════════════════════════
# INTEGRATED EVENT PIPELINE
# ═══════════════════════════════════════════════════════════════

class LegalEventPipeline:
    """
    Integrated pipeline: Crawler → Kafka → Processing → Storage.
    Connects all components for real-time legal intelligence.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.producer = LegalEventProducer()
        self.cache = RedisCache()
        logger.info("Legal Event Pipeline initialized")

    def process_crawler_event(self, event: Dict):
        """
        Process event from legal crawler.

        Args:
            event: Event from AdvancedLegalCrawler
        """
        # Publish to Kafka
        published = self.producer.publish_legal_event(event)

        # Cache high-priority events
        if event.get('risk_level') == 'HIGH':
            cache_key = f"event:{event.get('event_id')}"
            self.cache.set(cache_key, event, ttl=7200)  # 2 hours

        # Trigger simulation for high-risk events
        if published and event.get('risk_level') == 'HIGH':
            self._trigger_simulation(event)

        return published

    def process_risk_assessment(self, contract_id: str, risk_data: Dict):
        """Process risk assessment result."""
        # Publish to Kafka
        self.producer.publish_risk_assessment(contract_id, risk_data)

        # Cache result
        self.cache.cache_risk_score(contract_id, risk_data, ttl=3600)

        # Send alert if high risk
        if risk_data.get('legal_risk_level') == 'High':
            self.producer.publish_alert(
                alert_type='high_risk_contract',
                message=f"Contract {contract_id} has HIGH legal risk",
                severity='HIGH'
            )

    def _trigger_simulation(self, event: Dict):
        """Trigger what-if simulation for event."""
        simulation_event = {
            'event_id': f"sim_{event.get('event_id')}",
            'event_type': 'simulation_trigger',
            'source_event': event.get('event_id'),
            'timestamp': datetime.now().isoformat(),
            'data': event
        }
        self.producer.publish_legal_event(simulation_event, TOPICS['SIMULATION_TRIGGERS'])
        logger.info(f"Triggered simulation for event {event.get('event_id')}")


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════════

_producer_instance: Optional[LegalEventProducer] = None
_cache_instance: Optional[RedisCache] = None
_pipeline_instance: Optional[LegalEventPipeline] = None


def get_kafka_producer() -> LegalEventProducer:
    """Get singleton Kafka producer."""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = LegalEventProducer()
    return _producer_instance


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def get_event_pipeline() -> LegalEventPipeline:
    """Get singleton event pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = LegalEventPipeline()
    return _pipeline_instance
