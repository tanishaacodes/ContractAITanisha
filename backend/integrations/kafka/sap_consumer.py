"""
SAP Event Mesh / Kafka Consumer for PrimeContractAI

Listens for SAP S/4HANA business events and triggers AI analysis automatically.

Event topics consumed:
  - sap/s4/contract/created   → Scenario 1 (process new contract)
  - sap/s4/contract/amended   → Scenario 3 (amendment re-evaluation)
  - sap/s4/contract/blocked   → Scenario 2 (block high-risk check)

Usage:
    python -m integrations.kafka.sap_consumer

Or via Django management command:
    python manage.py run_sap_consumer
"""
import json
import asyncio
import logging
import os
import sys

logger = logging.getLogger(__name__)

# ── Kafka config from environment ────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID = os.getenv("KAFKA_SAP_GROUP_ID", "primecontractai-sap-consumer")
KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")

SAP_TOPICS = {
    "sap.s4.contract.created": "process",
    "sap.s4.contract.amended": "amendment",
    "sap.s4.contract.changed": "amendment",
    "sap.s4.contract.high_risk": "block",
}


class SAPEventConsumer:
    """
    Kafka consumer that listens for SAP S/4HANA business events
    and triggers the appropriate PrimeContractAI scenario.
    """

    def __init__(self):
        self.running = False
        self._consumer = None

    def _get_consumer(self):
        """Lazy-load Kafka consumer to avoid import errors if kafka-python not installed."""
        try:
            from kafka import KafkaConsumer
            return KafkaConsumer(
                *SAP_TOPICS.keys(),
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000,
            )
        except ImportError:
            logger.warning("kafka-python not installed. Install with: pip install kafka-python")
            return None
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return None

    async def _handle_event(self, topic: str, event: dict):
        """
        Route SAP event to the appropriate scenario handler.

        SAP Event Mesh BOD payload example:
        {
          "contractId": "4600001234",
          "eventType": "Contract.Created",
          "companyCode": "1000",
          "timestamp": "2026-02-17T10:30:00Z"
        }
        """
        contract_id = (
            event.get("contractId") or
            event.get("PurchaseContract") or
            event.get("contract_id")
        )

        if not contract_id:
            logger.warning(f"Event on {topic} has no contractId: {event}")
            return

        scenario = SAP_TOPICS.get(topic, "process")
        logger.info(f"[SAP EVENT] topic={topic} contract={contract_id} → scenario={scenario}")

        try:
            from integrations.sap.sap_contract_service import SAPContractService

            async with SAPContractService() as service:
                if scenario == "process":
                    result = await service.process_new_contract(contract_id)
                elif scenario == "amendment":
                    result = await service.process_amendment(contract_id)
                elif scenario == "block":
                    result = await service.block_high_risk_contract(contract_id)
                else:
                    result = await service.process_new_contract(contract_id)

            logger.info(f"[SAP EVENT] Processed {contract_id}: {result.get('status', result.get('message', 'done'))}")

        except Exception as e:
            logger.error(f"[SAP EVENT] Failed to process {contract_id}: {e}", exc_info=True)

    def start(self):
        """Start the Kafka consumer loop (blocking)."""
        logger.info(f"Starting SAP Event Consumer — topics: {list(SAP_TOPICS.keys())}")
        logger.info(f"Kafka broker: {KAFKA_BOOTSTRAP_SERVERS}")

        consumer = self._get_consumer()
        if consumer is None:
            logger.error("Cannot start SAP consumer — Kafka unavailable.")
            return

        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while self.running:
                for message in consumer:
                    if not self.running:
                        break
                    try:
                        logger.debug(
                            f"Received message: topic={message.topic} "
                            f"partition={message.partition} offset={message.offset}"
                        )
                        loop.run_until_complete(
                            self._handle_event(message.topic, message.value)
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
        except KeyboardInterrupt:
            logger.info("SAP Event Consumer stopped by user")
        finally:
            consumer.close()
            loop.close()
            logger.info("SAP Event Consumer shutdown complete")

    def stop(self):
        self.running = False


# ── Management command helper ─────────────────────────────────────────────────

def run_consumer():
    """Entry point for management command or direct execution."""
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contractai.settings")
    django.setup()

    consumer = SAPEventConsumer()
    consumer.start()


if __name__ == "__main__":
    run_consumer()
