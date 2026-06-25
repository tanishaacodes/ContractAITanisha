"""
Django Management Command: Train Dispute Predictor
===================================================
Trains the neural network dispute prediction model.

Usage:
    python manage.py train_dispute_predictor
    python manage.py train_dispute_predictor --epochs 200 --batch-size 64
"""

from django.core.management.base import BaseCommand
from dispute_predictor.train_dispute_model import train_model


class Command(BaseCommand):
    help = 'Train the dispute prediction neural network model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=100,
            help='Number of training epochs (default: 100)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='Training batch size (default: 32)'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=0.001,
            help='Initial learning rate (default: 0.001)'
        )
        parser.add_argument(
            '--val-split',
            type=float,
            default=0.2,
            help='Validation split ratio (default: 0.2)'
        )
        parser.add_argument(
            '--model-path',
            type=str,
            default='models/dispute_predictor.pth',
            help='Path to save trained model (default: models/dispute_predictor.pth)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting dispute predictor training...'))

        try:
            history = train_model(
                epochs=options['epochs'],
                batch_size=options['batch_size'],
                learning_rate=options['learning_rate'],
                val_split=options['val_split'],
                model_save_path=options['model_path']
            )

            self.stdout.write(self.style.SUCCESS('\n✅ Training completed successfully!'))
            self.stdout.write(f"   Final validation accuracy: {history['val_acc'][-1]:.1%}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Training failed: {str(e)}'))
            raise
