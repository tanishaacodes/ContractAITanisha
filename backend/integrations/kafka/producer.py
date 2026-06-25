"""
Kafka Producer for ContractAI Platform.
Publishes events to Kafka topics for event-driven microservices architecture.
"""
try:
    from confluent_kafka import Producer, KafkaError, KafkaException
except ImportError:
    Producer = None
    KafkaError = None
    KafkaException = Exception
from django.conf import settings
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_CLIENT_ID = getattr(settings, 'KAFKA_CLIENT_ID', 'contractai-django')

# Producer configuration
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': KAFKA_CLIENT_ID,
    'acks': 'all',  # Wait for all replicas to acknowledge
    'retries': 3,
    'max.in.flight.requests.per.connection': 1,  # Ensure ordering
    'compression.type': 'gzip',
    # Suppress librdkafka connection-retry noise when broker is unavailable
    'log_level': 0,          # 0 = no logs from librdkafka to stderr
    'reconnect.backoff.ms': 60000,      # wait 60s before retry
    'reconnect.backoff.max.ms': 300000, # max 5 min between retries
}

# Global producer instance (lazy initialization)
_producer = None


def get_producer() -> Producer:
    """
    Get or create the global Kafka producer instance.
    Uses lazy initialization to avoid connection issues at import time.
    """
    global _producer
    if _producer is None:
        try:
            _producer = Producer(producer_conf)
            logger.info(f"Kafka producer initialized: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            raise KafkaException(f"Producer initialization failed: {str(e)}")
    return _producer


def delivery_callback(err, msg):
    """
    Callback function for message delivery reports.
    Called once for each message produced to indicate success or failure.
    """
    if err:
        logger.error(f"Message delivery failed: {err}. Topic: {msg.topic()}, Partition: {msg.partition()}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")


def publish_event(topic: str, payload: Dict[str, Any], key: Optional[str] = None) -> bool:
    """
    Publish an event to a Kafka topic.

    Args:
        topic: Kafka topic name
        payload: Event payload (will be JSON-serialized)
        key: Optional message key for partitioning

    Returns:
        bool: True if message was successfully queued, False otherwise
    """
    try:
        producer = get_producer()

        # Serialize payload to JSON
        message_value = json.dumps(payload).encode('utf-8')

        # Encode key if provided
        message_key = key.encode('utf-8') if key else None

        # Produce message asynchronously
        producer.produce(
            topic=topic,
            key=message_key,
            value=message_value,
            callback=delivery_callback
        )

        # Trigger any available delivery report callbacks
        producer.poll(0)

        logger.info(f"Published event to {topic}. Key: {key}")
        return True

    except BufferError:
        logger.error(f"Local producer queue is full ({len(producer)} messages awaiting delivery)")
        # Flush and retry once
        producer.flush()
        return publish_event(topic, payload, key)

    except Exception as e:
        logger.error(f"Failed to publish event to {topic}: {str(e)}")
        return False


def publish_event_sync(topic: str, payload: Dict[str, Any], key: Optional[str] = None, timeout: float = 10.0) -> bool:
    """
    Publish an event synchronously (blocks until delivery confirmation).

    Args:
        topic: Kafka topic name
        payload: Event payload (will be JSON-serialized)
        key: Optional message key for partitioning
        timeout: Max time to wait for delivery (seconds)

    Returns:
        bool: True if message was successfully delivered, False otherwise
    """
    try:
        result = publish_event(topic, payload, key)
        if result:
            # Flush to ensure delivery
            producer = get_producer()
            producer.flush(timeout)
            logger.info(f"Event delivered synchronously to {topic}")
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to deliver event synchronously to {topic}: {str(e)}")
        return False


def flush_producer(timeout: float = 10.0):
    """
    Flush any outstanding messages.
    Blocks until all messages are delivered or timeout is reached.

    Args:
        timeout: Max time to wait (seconds)
    """
    try:
        producer = get_producer()
        remaining = producer.flush(timeout)
        if remaining > 0:
            logger.warning(f"{remaining} messages were not delivered within {timeout}s")
        else:
            logger.info("All messages flushed successfully")
    except Exception as e:
        logger.error(f"Error flushing producer: {str(e)}")


def close_producer():
    """
    Close the Kafka producer and release resources.
    """
    global _producer
    if _producer:
        try:
            flush_producer()
            _producer = None
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {str(e)}")


# ========================================
# CONTRACT EVENT PUBLISHERS
# ========================================

def publish_contract_uploaded(contract_id: str, user_id: str, filename: str):
    """
    Publish event when a contract is uploaded.

    Args:
        contract_id: UUID of the uploaded contract
        user_id: UUID of the user who uploaded it
        filename: Original filename
    """
    from django.utils import timezone
    payload = {
        "event_type": "contract.uploaded",
        "contract_id": contract_id,
        "user_id": user_id,
        "filename": filename,
        "timestamp": str(timezone.now().isoformat())
    }
    return publish_event("contract.ingest", payload, key=contract_id)


def publish_contract_review_request(contract_id: str, requested_by: str, action: str = "FULL_REVIEW"):
    """
    Publish event to request contract review by AI agents.

    Args:
        contract_id: UUID of the contract
        requested_by: Email of user requesting review
        action: Type of review (FULL_REVIEW, RISK_ONLY, etc.)
    """
    from django.utils import timezone

    payload = {
        "event_type": "contract.review.request",
        "contract_id": contract_id,
        "requested_by": requested_by,
        "action": action,
        "timestamp": timezone.now().isoformat()
    }
    return publish_event("contract.review.request", payload, key=contract_id)


def publish_contract_risk_request(contract_id: str, requested_by: str):
    """
    Publish event to request risk analysis for a contract.

    Args:
        contract_id: UUID of the contract
        requested_by: Email of user requesting analysis
    """
    from django.utils import timezone

    payload = {
        "event_type": "contract.risk.request",
        "contract_id": contract_id,
        "requested_by": requested_by,
        "timestamp": timezone.now().isoformat()
    }
    return publish_event("contract.risk.request", payload, key=contract_id)


def publish_contract_drift_request(contract_id: str, requested_by: str):
    """
    Publish event to request drift detection for a contract.

    Args:
        contract_id: UUID of the contract
        requested_by: Email of user requesting detection
    """
    from django.utils import timezone

    payload = {
        "event_type": "contract.drift.request",
        "contract_id": contract_id,
        "requested_by": requested_by,
        "timestamp": timezone.now().isoformat()
    }
    return publish_event("contract.drift.request", payload, key=contract_id)


# ========================================
# FIVETRAN EVENT PUBLISHERS
# ========================================

def publish_fivetran_sync_completed(schema: str, connector_id: str, records_synced: int):
    """
    Publish event when Fivetran sync completes.

    Args:
        schema: Fivetran schema name
        connector_id: Fivetran connector ID
        records_synced: Number of records synced
    """
    from django.utils import timezone

    payload = {
        "event_type": "fivetran.sync.completed",
        "schema": schema,
        "connector_id": connector_id,
        "records_synced": records_synced,
        "timestamp": timezone.now().isoformat()
    }
    return publish_event("integration.fivetran.sync", payload, key=connector_id)
