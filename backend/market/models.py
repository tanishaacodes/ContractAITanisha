from django.db import models


class MarketSignal(models.Model):
    """Stores fetched market signal snapshots for historical tracking."""

    SIGNAL_TYPES = [
        ('commodity', 'Commodity'),
        ('interest_rate', 'Interest Rate'),
        ('fx', 'Foreign Exchange'),
        ('equity', 'Equity Index'),
    ]

    signal_type = models.CharField(max_length=50, choices=SIGNAL_TYPES)
    signal_name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=50, blank=True, null=True)
    current_value = models.FloatField(null=True, blank=True)
    previous_value = models.FloatField(null=True, blank=True)
    percent_change = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default='live')
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fetched_at']
        indexes = [
            models.Index(fields=['signal_type', 'fetched_at']),
        ]

    def __str__(self):
        return f"{self.signal_name} @ {self.current_value} ({self.percent_change:+.2f}%)"
