"""
Django management command to run Kafka agent orchestrator consumer.
Usage: python manage.py run_kafka_agent_consumer
"""
from django.core.management.base import BaseCommand
from integrations.kafka.consumer import run_agent_orchestrator
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Kafka agent orchestrator consumer (listens for contract analysis requests)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            help='Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)'
        )

    def handle(self, *args, **options):
        log_level = options['log_level'].upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )

        self.stdout.write(self.style.SUCCESS('Starting Kafka Agent Orchestrator Consumer...'))
        self.stdout.write(self.style.WARNING('Press Ctrl+C to stop'))
        self.stdout.write(self.style.NOTICE('Listening to topics:'))
        self.stdout.write('  - contract.review.request')
        self.stdout.write('  - contract.risk.request')
        self.stdout.write('  - contract.drift.request')
        self.stdout.write('')

        try:
            run_agent_orchestrator()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping consumer...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Consumer error: {str(e)}'))
            raise
