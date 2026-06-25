"""
Django management command to run Kafka Django results consumer.
Usage: python manage.py run_kafka_django_consumer
"""
from django.core.management.base import BaseCommand
from integrations.kafka.consumer import run_django_results
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Kafka Django results consumer (listens for analysis completion events)'

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

        self.stdout.write(self.style.SUCCESS('Starting Kafka Django Results Consumer...'))
        self.stdout.write(self.style.WARNING('Press Ctrl+C to stop'))
        self.stdout.write(self.style.NOTICE('Listening to topics:'))
        self.stdout.write('  - contract.review.completed')
        self.stdout.write('  - contract.risk.scored')
        self.stdout.write('  - contract.drift.detected')
        self.stdout.write('  - contract.failed')
        self.stdout.write('')

        try:
            run_django_results()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping consumer...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Consumer error: {str(e)}'))
            raise
