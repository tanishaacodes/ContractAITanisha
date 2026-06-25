"""
Legal Events Kafka Consumer
============================
Consumes messages from the 'legal_events' Kafka topic and:
1. Stores them in _LIVE_EVENTS (in-memory feed)
2. Pushes to _WS_BROADCAST_QUEUE (SSE polling)
3. Triggers auto what-if simulation per event

Run as a management command: python manage.py run_legal_kafka_consumer
Or started automatically by the Django app on startup (background thread).
"""
import json
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

_consumer_thread = None
_consumer_running = False


def _run_consumer():
    """Background thread: consume legal_events from Kafka."""
    global _consumer_running

    try:
        from confluent_kafka import Consumer, KafkaError
        from django.conf import settings
    except ImportError:
        logger.warning("[LEGAL-KAFKA] confluent_kafka not installed, consumer not started")
        return

    broker = getattr(settings, 'KAFKA_BROKER_URL', 'localhost:9092')
    conf = {
        'bootstrap.servers': broker,
        'group.id': 'legal-review-consumer-group',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 5000,
        'log_level': 0,
        'reconnect.backoff.ms': 10000,
        'reconnect.backoff.max.ms': 60000,
        'session.timeout.ms': 30000,
        'heartbeat.interval.ms': 10000,
    }

    consumer = None
    try:
        consumer = Consumer(conf)
        consumer.subscribe(['legal_events'])
        logger.info(f"[LEGAL-KAFKA] Consumer started, broker={broker}, topic=legal_events")
    except Exception as e:
        logger.warning(f"[LEGAL-KAFKA] Consumer init failed: {e}")
        return

    _consumer_running = True
    while _consumer_running:
        try:
            msg = consumer.poll(timeout=2.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.warning(f"[LEGAL-KAFKA] Consumer error: {msg.error()}")
                time.sleep(2)
                continue

            # Parse and store the event
            try:
                event = json.loads(msg.value().decode('utf-8'))
                _handle_consumed_event(event)
            except Exception as parse_err:
                logger.warning(f"[LEGAL-KAFKA] Failed to parse message: {parse_err}")

        except Exception as e:
            logger.warning(f"[LEGAL-KAFKA] Poll error: {e}")
            time.sleep(5)

    if consumer:
        try:
            consumer.close()
        except Exception:
            pass
    logger.info("[LEGAL-KAFKA] Consumer stopped")


def _handle_consumed_event(event: dict):
    """
    Handle a legal event consumed from Kafka.
    Stores it in the live feed and SSE broadcast queue.
    """
    try:
        # Import here to avoid circular imports
        from api.legal_review_views import (
            _LIVE_EVENTS, _EVENTS_LOCK,
            _WS_BROADCAST_QUEUE, _WS_LOCK,
        )

        # Add consumed_via marker
        event['consumed_via_kafka'] = True
        if 'timestamp' not in event:
            event['timestamp'] = datetime.now().isoformat()

        # Store in live events feed
        with _EVENTS_LOCK:
            # Deduplicate by event_id
            existing_ids = {e.get('event_id') for e in _LIVE_EVENTS}
            if event.get('event_id') not in existing_ids:
                _LIVE_EVENTS.insert(0, event)
                if len(_LIVE_EVENTS) > 200:
                    _LIVE_EVENTS.pop()

        # Push to SSE broadcast queue
        with _WS_LOCK:
            _WS_BROADCAST_QUEUE.append(event)
            if len(_WS_BROADCAST_QUEUE) > 100:
                _WS_BROADCAST_QUEUE.pop(0)

        logger.info(f"[LEGAL-KAFKA] Consumed event: {event.get('event_id')} | {event.get('title', '')[:60]}")

    except Exception as e:
        logger.warning(f"[LEGAL-KAFKA] Failed to handle event: {e}")


def start_consumer():
    """Start the Kafka consumer in a background daemon thread."""
    global _consumer_thread, _consumer_running

    if _consumer_thread and _consumer_thread.is_alive():
        return  # Already running

    from django.conf import settings
    if not getattr(settings, 'KAFKA_ENABLED', False):
        logger.info("[LEGAL-KAFKA] KAFKA_ENABLED=False, consumer not started")
        return

    _consumer_running = False
    _consumer_thread = threading.Thread(
        target=_run_consumer,
        name="legal-kafka-consumer",
        daemon=True,
    )
    _consumer_thread.start()
    logger.info("[LEGAL-KAFKA] Consumer thread launched")


def stop_consumer():
    """Signal the consumer thread to stop."""
    global _consumer_running
    _consumer_running = False
