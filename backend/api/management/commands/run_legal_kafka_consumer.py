"""
Management command: python manage.py run_legal_kafka_consumer

Runs the Legal Events Kafka consumer in the foreground.
Useful for running as a separate process in production.
"""
import signal
import time
from django.core.management.base import BaseCommand
from api.legal_kafka_consumer import start_consumer, stop_consumer


class Command(BaseCommand):
    help = 'Run the Legal Events Kafka consumer (topic: legal_events)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '[LEGAL-KAFKA] Starting consumer for topic: legal_events'
        ))

        def _shutdown(signum, frame):
            self.stdout.write(self.style.WARNING('\n[LEGAL-KAFKA] Shutting down...'))
            stop_consumer()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        start_consumer()

        self.stdout.write(self.style.SUCCESS(
            '[LEGAL-KAFKA] Consumer running. Press Ctrl+C to stop.'
        ))

        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_consumer()
            self.stdout.write(self.style.SUCCESS('[LEGAL-KAFKA] Consumer stopped.'))
