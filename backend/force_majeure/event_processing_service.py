"""
Event Processing Service
Simplified streaming architecture for Force Majeure event processing
Alternative to Kafka for real-time FM event monitoring
"""

import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class FMEvent:
    """Force Majeure event"""
    event_id: str
    event_type: str
    severity: float
    region: str
    source: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    affected_contracts: List[str] = field(default_factory=list)


@dataclass
class EventSubscription:
    """Event subscription"""
    subscription_id: str
    event_types: List[str]
    regions: List[str]
    severity_threshold: float
    callback: Optional[Callable] = None
    webhook_url: Optional[str] = None


class EventStream:
    """In-memory event stream"""

    def __init__(self, max_size: int = 10000):
        self.events = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def publish(self, event: FMEvent):
        """Publish event to stream"""
        with self.lock:
            self.events.append(event)
            logger.info(f"Published event {event.event_id} to stream")

    def consume(self, since: Optional[datetime] = None, limit: int = 100) -> List[FMEvent]:
        """Consume events from stream"""
        with self.lock:
            if since:
                filtered = [e for e in self.events if e.timestamp >= since]
            else:
                filtered = list(self.events)

            return filtered[-limit:]

    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[FMEvent]:
        """Get events by type"""
        with self.lock:
            filtered = [e for e in self.events if e.event_type == event_type]
            return filtered[-limit:]

    def get_events_by_region(self, region: str, limit: int = 100) -> List[FMEvent]:
        """Get events by region"""
        with self.lock:
            filtered = [e for e in self.events if e.region == region]
            return filtered[-limit:]


class EventProcessor:
    """Process and transform FM events"""

    def __init__(self):
        self.processors: Dict[str, Callable] = {}

    def register_processor(self, event_type: str, processor: Callable):
        """Register event processor"""
        self.processors[event_type] = processor
        logger.info(f"Registered processor for event type: {event_type}")

    def process(self, event: FMEvent) -> FMEvent:
        """Process event"""
        if event.event_type in self.processors:
            processor = self.processors[event.event_type]
            try:
                event = processor(event)
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")

        return event


class EventRouter:
    """Route events to subscribers"""

    def __init__(self):
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.lock = threading.Lock()

    def subscribe(
        self,
        subscription_id: str,
        event_types: List[str],
        regions: List[str],
        severity_threshold: float = 0.0,
        callback: Optional[Callable] = None,
        webhook_url: Optional[str] = None
    ) -> str:
        """Subscribe to events"""
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=event_types,
            regions=regions,
            severity_threshold=severity_threshold,
            callback=callback,
            webhook_url=webhook_url
        )

        with self.lock:
            self.subscriptions[subscription_id] = subscription

        logger.info(f"Created subscription {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        with self.lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                logger.info(f"Removed subscription {subscription_id}")

    def route(self, event: FMEvent):
        """Route event to matching subscribers"""
        with self.lock:
            subscribers = list(self.subscriptions.values())

        for sub in subscribers:
            if self._matches_subscription(event, sub):
                self._notify_subscriber(event, sub)

    def _matches_subscription(self, event: FMEvent, subscription: EventSubscription) -> bool:
        """Check if event matches subscription"""

        # Check event type
        if subscription.event_types and event.event_type not in subscription.event_types:
            return False

        # Check region
        if subscription.regions and event.region not in subscription.regions:
            return False

        # Check severity
        if event.severity < subscription.severity_threshold:
            return False

        return True

    def _notify_subscriber(self, event: FMEvent, subscription: EventSubscription):
        """Notify subscriber of event"""
        try:
            if subscription.callback:
                subscription.callback(event)

            if subscription.webhook_url:
                # In production, would make HTTP POST to webhook
                logger.info(f"Would notify webhook {subscription.webhook_url} for event {event.event_id}")

        except Exception as e:
            logger.error(f"Error notifying subscriber {subscription.subscription_id}: {e}")


class EventAggregator:
    """Aggregate events for analysis"""

    def __init__(self):
        self.aggregations: Dict[str, List[FMEvent]] = {}

    def aggregate_by_time_window(
        self,
        events: List[FMEvent],
        window_minutes: int = 60
    ) -> Dict[str, List[FMEvent]]:
        """Aggregate events by time window"""

        if not events:
            return {}

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        windows = {}
        window_start = sorted_events[0].timestamp
        window_end = window_start + timedelta(minutes=window_minutes)
        window_key = window_start.strftime('%Y-%m-%d %H:%M')

        current_window = []

        for event in sorted_events:
            if event.timestamp < window_end:
                current_window.append(event)
            else:
                windows[window_key] = current_window

                # Start new window
                window_start = event.timestamp
                window_end = window_start + timedelta(minutes=window_minutes)
                window_key = window_start.strftime('%Y-%m-%d %H:%M')
                current_window = [event]

        # Add final window
        if current_window:
            windows[window_key] = current_window

        return windows

    def aggregate_by_region(self, events: List[FMEvent]) -> Dict[str, List[FMEvent]]:
        """Aggregate events by region"""

        regions = {}
        for event in events:
            if event.region not in regions:
                regions[event.region] = []
            regions[event.region].append(event)

        return regions

    def aggregate_by_type(self, events: List[FMEvent]) -> Dict[str, List[FMEvent]]:
        """Aggregate events by type"""

        types = {}
        for event in events:
            if event.event_type not in types:
                types[event.event_type] = []
            types[event.event_type].append(event)

        return types


class EventProcessingService:
    """
    Complete event processing service for FM events

    Features:
    - Event ingestion and publishing
    - Real-time event streaming
    - Event processing and transformation
    - Event routing to subscribers
    - Event aggregation and analysis
    """

    def __init__(self):
        self.stream = EventStream(max_size=10000)
        self.processor = EventProcessor()
        self.router = EventRouter()
        self.aggregator = EventAggregator()
        self.running = False
        self.processor_thread = None

    def start(self):
        """Start event processing service"""
        if not self.running:
            self.running = True
            self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.processor_thread.start()
            logger.info("Event processing service started")

    def stop(self):
        """Stop event processing service"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Event processing service stopped")

    def publish_event(
        self,
        event_type: str,
        severity: float,
        region: str,
        source: str,
        metadata: Optional[Dict] = None,
        affected_contracts: Optional[List[str]] = None
    ) -> str:
        """
        Publish FM event to stream

        Args:
            event_type: Type of FM event (war, pandemic, etc.)
            severity: Event severity 0-1
            region: Geographic region
            source: Event source (news, sensor, user, etc.)
            metadata: Additional event data
            affected_contracts: List of affected contract IDs

        Returns:
            event_id: Unique event identifier
        """

        event_id = f"evt_{int(datetime.now().timestamp() * 1000)}"

        event = FMEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            region=region,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {},
            affected_contracts=affected_contracts or []
        )

        # Process event
        event = self.processor.process(event)

        # Publish to stream
        self.stream.publish(event)

        # Route to subscribers
        self.router.route(event)

        return event_id

    def consume_events(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Consume events from stream"""

        events = self.stream.consume(since, limit)
        return [self._event_to_dict(e) for e in events]

    def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get events by type"""

        events = self.stream.get_events_by_type(event_type, limit)
        return [self._event_to_dict(e) for e in events]

    def get_events_by_region(
        self,
        region: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get events by region"""

        events = self.stream.get_events_by_region(region, limit)
        return [self._event_to_dict(e) for e in events]

    def subscribe_to_events(
        self,
        subscription_id: str,
        event_types: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        severity_threshold: float = 0.0,
        callback: Optional[Callable] = None,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Subscribe to FM events

        Args:
            subscription_id: Unique subscription identifier
            event_types: List of event types to subscribe to (None = all)
            regions: List of regions to subscribe to (None = all)
            severity_threshold: Minimum severity threshold
            callback: Optional callback function
            webhook_url: Optional webhook URL

        Returns:
            subscription_id
        """

        return self.router.subscribe(
            subscription_id,
            event_types or [],
            regions or [],
            severity_threshold,
            callback,
            webhook_url
        )

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        self.router.unsubscribe(subscription_id)

    def get_aggregated_events(
        self,
        aggregation_type: str = 'region',
        time_window_minutes: Optional[int] = None
    ) -> Dict:
        """
        Get aggregated events

        Args:
            aggregation_type: 'region', 'type', or 'time'
            time_window_minutes: Time window for temporal aggregation

        Returns:
            Aggregated events
        """

        events = self.stream.consume()

        if aggregation_type == 'region':
            aggregated = self.aggregator.aggregate_by_region(events)
        elif aggregation_type == 'type':
            aggregated = self.aggregator.aggregate_by_type(events)
        elif aggregation_type == 'time' and time_window_minutes:
            aggregated = self.aggregator.aggregate_by_time_window(events, time_window_minutes)
        else:
            return {'error': 'Invalid aggregation type'}

        # Convert to dict format
        result = {}
        for key, event_list in aggregated.items():
            result[key] = {
                'count': len(event_list),
                'events': [self._event_to_dict(e) for e in event_list],
                'average_severity': sum(e.severity for e in event_list) / len(event_list) if event_list else 0
            }

        return result

    def get_event_statistics(self) -> Dict:
        """Get event stream statistics"""

        events = self.stream.consume()

        if not events:
            return {
                'total_events': 0,
                'event_types': {},
                'regions': {},
                'average_severity': 0
            }

        # Calculate statistics
        event_types = {}
        regions = {}
        total_severity = 0

        for event in events:
            # Count by type
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

            # Count by region
            regions[event.region] = regions.get(event.region, 0) + 1

            # Sum severity
            total_severity += event.severity

        return {
            'total_events': len(events),
            'event_types': event_types,
            'regions': regions,
            'average_severity': round(total_severity / len(events), 3),
            'oldest_event': events[0].timestamp.isoformat() if events else None,
            'newest_event': events[-1].timestamp.isoformat() if events else None
        }

    def _process_loop(self):
        """Background processing loop"""
        while self.running:
            try:
                # Placeholder for background processing tasks
                # Could include: cleanup old events, aggregate statistics, etc.
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

    def _event_to_dict(self, event: FMEvent) -> Dict:
        """Convert event to dictionary"""
        return {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'severity': event.severity,
            'region': event.region,
            'source': event.source,
            'timestamp': event.timestamp.isoformat(),
            'metadata': event.metadata,
            'affected_contracts': event.affected_contracts
        }

    def register_event_processor(self, event_type: str, processor: Callable):
        """Register custom event processor"""
        self.processor.register_processor(event_type, processor)


# Global instance
event_processing_service = EventProcessingService()


# Auto-start service
event_processing_service.start()


# Convenience functions
def publish_fm_event(
    event_type: str,
    severity: float,
    region: str,
    source: str = 'system',
    metadata: Optional[Dict] = None,
    affected_contracts: Optional[List[str]] = None
) -> str:
    """Publish FM event"""
    return event_processing_service.publish_event(
        event_type,
        severity,
        region,
        source,
        metadata,
        affected_contracts
    )


def consume_fm_events(since: Optional[datetime] = None, limit: int = 100) -> List[Dict]:
    """Consume FM events"""
    return event_processing_service.consume_events(since, limit)


def subscribe_to_fm_events(
    subscription_id: str,
    event_types: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    severity_threshold: float = 0.0
) -> str:
    """Subscribe to FM events"""
    return event_processing_service.subscribe_to_events(
        subscription_id,
        event_types,
        regions,
        severity_threshold
    )
