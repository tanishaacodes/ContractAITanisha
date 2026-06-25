"""
Kafka Consumer for ContractAI Platform.
Listens to Kafka topics and processes events for AI agent orchestration.
"""
try:
    from confluent_kafka import Consumer, KafkaError, KafkaException
except ImportError:
    Consumer = None
    KafkaError = None
    KafkaException = Exception
from django.conf import settings
import json
import logging
import signal
import sys
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Running flag for graceful shutdown
_running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _running
    logger.info(f"Received signal {signum}. Shutting down consumer...")
    _running = False


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class ContractAIConsumer:
    """
    Base consumer class for ContractAI Kafka consumers.
    """

    def __init__(self, group_id: str, topics: list, auto_offset_reset: str = 'earliest'):
        """
        Initialize the Kafka consumer.

        Args:
            group_id: Consumer group ID
            topics: List of topics to subscribe to
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.group_id = group_id
        self.topics = topics

        self.consumer_conf = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': False,  # Manual commit for reliability
            'max.poll.interval.ms': 300000,  # 5 minutes
            'session.timeout.ms': 30000,  # 30 seconds
        }

        self.consumer = None
        self.message_handlers: Dict[str, Callable] = {}

    def connect(self):
        """Connect to Kafka and subscribe to topics."""
        try:
            self.consumer = Consumer(self.consumer_conf)
            self.consumer.subscribe(self.topics)
            logger.info(f"Consumer {self.group_id} subscribed to: {', '.join(self.topics)}")
        except Exception as e:
            logger.error(f"Failed to create consumer: {str(e)}")
            raise KafkaException(f"Consumer initialization failed: {str(e)}")

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a message handler for a specific event type.

        Args:
            event_type: Event type string (e.g., 'contract.review.request')
            handler: Callable that takes (event_data: dict) as argument
        """
        self.message_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    def process_message(self, msg):
        """
        Process a single Kafka message.

        Args:
            msg: Kafka message object
        """
        try:
            # Decode message
            message_value = msg.value().decode('utf-8')
            event_data = json.loads(message_value)

            logger.debug(f"Processing message from {msg.topic()}: {event_data}")

            # Extract event type
            event_type = event_data.get('event_type')

            if not event_type:
                logger.warning(f"Message missing event_type: {event_data}")
                return

            # Find and execute handler
            handler = self.message_handlers.get(event_type)

            if handler:
                logger.info(f"Executing handler for {event_type}")
                handler(event_data)
            else:
                logger.warning(f"No handler registered for event type: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise

    def consume(self, poll_timeout: float = 1.0):
        """
        Start consuming messages.

        Args:
            poll_timeout: Timeout for each poll (seconds)
        """
        global _running

        if not self.consumer:
            self.connect()

        logger.info(f"Starting consumer loop for group: {self.group_id}")

        try:
            while _running:
                msg = self.consumer.poll(timeout=poll_timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition - not an error
                        logger.debug(f"Reached end of partition {msg.partition()} @ offset {msg.offset()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        raise KafkaException(msg.error())
                else:
                    # Process message
                    self.process_message(msg)

                    # Commit offset after successful processing
                    self.consumer.commit(asynchronous=False)

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
        finally:
            self.close()

    def close(self):
        """Close the consumer and release resources."""
        if self.consumer:
            logger.info(f"Closing consumer: {self.group_id}")
            self.consumer.close()
            self.consumer = None


# ========================================
# AGENT ORCHESTRATOR CONSUMER
# ========================================

class AgentOrchestratorConsumer(ContractAIConsumer):
    """
    Consumer that feeds contract analysis requests to AI agents.
    """

    def __init__(self):
        super().__init__(
            group_id='contract-ai-agents',
            topics=[
                'contract.review.request',
                'contract.risk.request',
                'contract.drift.request',
            ],
            auto_offset_reset='earliest'
        )

        # Register handlers
        self.register_handler('contract.review.request', self.handle_review_request)
        self.register_handler('contract.risk.request', self.handle_risk_request)
        self.register_handler('contract.drift.request', self.handle_drift_request)

    def handle_review_request(self, event_data: dict):
        """
        Handle contract review request event.

        Args:
            event_data: Event payload
        """
        contract_id = event_data.get('contract_id')
        action = event_data.get('action', 'FULL_REVIEW')

        logger.info(f"Handling review request for contract: {contract_id}, action: {action}")

        try:
            # Import here to avoid circular imports
            from agents.contract_agent import run_analysis_workflow

            # Trigger agent analysis
            import asyncio
            result = asyncio.run(run_analysis_workflow(
                contract_id=contract_id,
                mode='full' if action == 'FULL_REVIEW' else 'auto'
            ))

            # Publish result back to Kafka
            from .producer import publish_event
            publish_event(
                topic='contract.review.completed',
                payload={
                    "event_type": "contract.review.completed",
                    "contract_id": contract_id,
                    "status": result.get('status'),
                    "results": result
                },
                key=contract_id
            )

            logger.info(f"Review completed for contract: {contract_id}")

        except Exception as e:
            logger.error(f"Failed to process review request: {str(e)}", exc_info=True)

            # Publish failure event
            from .producer import publish_event
            publish_event(
                topic='contract.failed',
                payload={
                    "event_type": "contract.failed",
                    "contract_id": contract_id,
                    "error": str(e)
                },
                key=contract_id
            )

    def handle_risk_request(self, event_data: dict):
        """
        Handle contract risk analysis request event.

        Args:
            event_data: Event payload
        """
        contract_id = event_data.get('contract_id')

        logger.info(f"Handling risk request for contract: {contract_id}")

        try:
            # Import here to avoid circular imports
            from agents.contract_agent import run_analysis_workflow

            # Trigger risk analysis
            import asyncio
            result = asyncio.run(run_analysis_workflow(
                contract_id=contract_id,
                mode='risk'
            ))

            # Publish result back to Kafka
            from .producer import publish_event
            publish_event(
                topic='contract.risk.scored',
                payload={
                    "event_type": "contract.risk.scored",
                    "contract_id": contract_id,
                    "risk_score": result.get('results', {}).get('risk_analysis', {}).get('risk_score'),
                    "risk_level": result.get('results', {}).get('risk_analysis', {}).get('risk_level'),
                    "results": result
                },
                key=contract_id
            )

            logger.info(f"Risk analysis completed for contract: {contract_id}")

        except Exception as e:
            logger.error(f"Failed to process risk request: {str(e)}", exc_info=True)

            # Publish failure event
            from .producer import publish_event
            publish_event(
                topic='contract.failed',
                payload={
                    "event_type": "contract.failed",
                    "contract_id": contract_id,
                    "error": str(e)
                },
                key=contract_id
            )

    def handle_drift_request(self, event_data: dict):
        """
        Handle contract drift detection request event.

        Args:
            event_data: Event payload
        """
        contract_id = event_data.get('contract_id')

        logger.info(f"Handling drift request for contract: {contract_id}")

        try:
            # TODO: Implement drift detection logic
            # For now, just acknowledge receipt
            from .producer import publish_event
            publish_event(
                topic='contract.drift.detected',
                payload={
                    "event_type": "contract.drift.detected",
                    "contract_id": contract_id,
                    "drift_detected": False,
                    "message": "Drift detection not yet implemented"
                },
                key=contract_id
            )

            logger.info(f"Drift detection completed for contract: {contract_id}")

        except Exception as e:
            logger.error(f"Failed to process drift request: {str(e)}", exc_info=True)


# ========================================
# DJANGO RESULT CONSUMER
# ========================================

class DjangoResultConsumer(ContractAIConsumer):
    """
    Consumer that listens for analysis results and updates Django database/UI.
    """

    def __init__(self):
        super().__init__(
            group_id='django-results',
            topics=[
                'contract.review.completed',
                'contract.risk.scored',
                'contract.drift.detected',
                'contract.failed',
            ],
            auto_offset_reset='latest'
        )

        # Register handlers
        self.register_handler('contract.review.completed', self.handle_review_completed)
        self.register_handler('contract.risk.scored', self.handle_risk_scored)
        self.register_handler('contract.drift.detected', self.handle_drift_detected)
        self.register_handler('contract.failed', self.handle_failed)

    def handle_review_completed(self, event_data: dict):
        """Handle contract review completion event."""
        contract_id = event_data.get('contract_id')
        status = event_data.get('status')
        results = event_data.get('results', {})

        logger.info(f"Review completed for contract: {contract_id}")

        try:
            from core.models import Contract, AnalysisResult
            from django.utils import timezone

            # Update contract processing status
            contract = Contract.objects.filter(id=contract_id).first()
            if contract:
                contract.last_analyzed_at = timezone.now()
                contract.processing_status = 'completed'
                contract.save()
                logger.info(f"Updated contract {contract_id} status to completed")

            # Store analysis results if provided
            if results:
                analysis_result = AnalysisResult.objects.filter(contract_id=contract_id).first()
                if analysis_result:
                    # Update existing result with completion timestamp
                    analysis_result.updated_at = timezone.now()
                    analysis_result.save()
                    logger.info(f"Updated analysis result for contract {contract_id}")

            # Send notification (placeholder for WebSocket/SSE implementation)
            logger.info(f"[Notification] Analysis completed for contract {contract_id}")
            # TODO: Implement WebSocket notification:
            # from channels.layers import get_channel_layer
            # await channel_layer.group_send(f"user_{user_id}", {...})

        except Exception as e:
            logger.error(f"Error handling review completion: {str(e)}", exc_info=True)

    def handle_risk_scored(self, event_data: dict):
        """Handle risk scoring completion event."""
        contract_id = event_data.get('contract_id')
        risk_score = event_data.get('risk_score')
        risk_level = event_data.get('risk_level')
        results = event_data.get('results', {})

        logger.info(f"Risk scored for contract {contract_id}: {risk_score} ({risk_level})")

        try:
            from core.models import Contract, AnalysisResult
            from django.utils import timezone

            # Update contract with risk information
            contract = Contract.objects.filter(id=contract_id).first()
            if contract:
                contract.risk_score = risk_score
                contract.risk_level = risk_level
                contract.last_risk_analysis_at = timezone.now()
                contract.save()
                logger.info(f"Updated risk scores for contract {contract_id}")

            # Update analysis result
            analysis_result = AnalysisResult.objects.filter(contract_id=contract_id).first()
            if analysis_result:
                analysis_result.risk_score = risk_score
                analysis_result.risk_level = risk_level
                analysis_result.updated_at = timezone.now()
                analysis_result.save()

            # Send high-risk alert if needed
            if risk_level in ['HIGH', 'CRITICAL']:
                logger.warning(f"[ALERT] High-risk contract detected: {contract_id} - {risk_level}")
                # TODO: Send email/Slack notification to legal team
                # send_risk_alert(contract_id, risk_level, risk_score)

        except Exception as e:
            logger.error(f"Error handling risk scored event: {str(e)}", exc_info=True)

    def handle_drift_detected(self, event_data: dict):
        """Handle drift detection event."""
        contract_id = event_data.get('contract_id')
        drift_detected = event_data.get('drift_detected', False)
        drift_details = event_data.get('drift_details', {})

        logger.info(f"Drift detection for contract {contract_id}: {drift_detected}")

        try:
            from core.models import Contract
            from django.utils import timezone

            if drift_detected:
                # Create drift alert record
                contract = Contract.objects.filter(id=contract_id).first()
                if contract:
                    # Store drift information
                    contract.drift_detected = True
                    contract.drift_detected_at = timezone.now()
                    contract.drift_details = drift_details
                    contract.save()

                    logger.warning(f"[DRIFT ALERT] Contract {contract_id} has drifted from baseline")

                    # TODO: Create DriftAlert model and record
                    # DriftAlert.objects.create(
                    #     contract=contract,
                    #     drift_type=drift_details.get('type'),
                    #     severity=drift_details.get('severity'),
                    #     details=drift_details
                    # )

                    # TODO: Notify contract owner
                    # send_drift_notification(contract_id, drift_details)

        except Exception as e:
            logger.error(f"Error handling drift detection: {str(e)}", exc_info=True)

    def handle_failed(self, event_data: dict):
        """Handle failed processing event."""
        contract_id = event_data.get('contract_id')
        error = event_data.get('error')
        failed_task = event_data.get('failed_task', 'unknown')

        logger.error(f"Processing failed for contract {contract_id}: {error}")

        try:
            from core.models import Contract
            from django.utils import timezone

            # Update contract with error status
            contract = Contract.objects.filter(id=contract_id).first()
            if contract:
                contract.processing_status = 'failed'
                contract.last_error = error
                contract.last_error_at = timezone.now()
                contract.save()

                logger.error(f"Marked contract {contract_id} as failed")

                # TODO: Create ErrorLog model and record
                # ErrorLog.objects.create(
                #     contract=contract,
                #     error_type='processing_failed',
                #     error_message=error,
                #     failed_task=failed_task,
                #     stack_trace=event_data.get('stack_trace')
                # )

                # TODO: Notify user and admin
                # send_error_notification(contract.user, contract_id, error)

        except Exception as e:
            logger.error(f"Error handling failed event: {str(e)}", exc_info=True)


# ========================================
# MAIN CONSUMER RUNNER
# ========================================

def run_agent_orchestrator():
    """
    Main entry point for running the agent orchestrator consumer.
    """
    logger.info("Starting Agent Orchestrator Consumer...")
    consumer = AgentOrchestratorConsumer()
    consumer.consume()


def run_django_results():
    """
    Main entry point for running the Django results consumer.
    """
    logger.info("Starting Django Results Consumer...")
    consumer = DjangoResultConsumer()
    consumer.consume()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python consumer.py [agent|django]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "agent":
        run_agent_orchestrator()
    elif mode == "django":
        run_django_results()
    else:
        print(f"Unknown mode: {mode}. Use 'agent' or 'django'")
        sys.exit(1)
