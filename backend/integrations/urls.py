"""
URL configuration for Fivetran and Kafka integration endpoints.
Fivetran endpoints require fivetran_access permission.
Kafka endpoints require kafka_access permission.
"""
from django.urls import path
from . import fivetran_views, kafka_views

urlpatterns = [
    # Fivetran Integration Endpoints
    path('fivetran/status/', fivetran_views.fivetran_status, name='fivetran_status'),
    path('fivetran/sync/', fivetran_views.fivetran_sync, name='fivetran_sync'),
    path('fivetran/connectors/', fivetran_views.fivetran_connectors, name='fivetran_connectors'),
    path('fivetran/webhook/', fivetran_views.fivetran_webhook, name='fivetran_webhook'),

    # Kafka Integration Endpoints
    path('kafka/status/', kafka_views.kafka_status, name='kafka_status'),
    path('kafka/topics/', kafka_views.kafka_topics, name='kafka_topics'),
    path('kafka/publish/', kafka_views.kafka_publish, name='kafka_publish'),
    path('kafka/consumer-groups/', kafka_views.kafka_consumer_groups, name='kafka_consumer_groups'),
    path('kafka/metrics/', kafka_views.kafka_metrics, name='kafka_metrics'),
    path('kafka/create-topics/', kafka_views.kafka_create_topics, name='kafka_create_topics'),
]
