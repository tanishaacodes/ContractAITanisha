"""
Kafka Integration API Views.
Only users with kafka_access permission (or SuperAdmin) can access these endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import require_kafka_access
try:
    from confluent_kafka.admin import AdminClient, NewTopic
    from confluent_kafka import KafkaException
    _KAFKA_AVAILABLE = True
except ImportError:
    AdminClient = None
    NewTopic = None
    KafkaException = Exception
    _KAFKA_AVAILABLE = False
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Kafka admin client configuration
KAFKA_BOOTSTRAP_SERVERS = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


def get_admin_client():
    """Get Kafka admin client instance."""
    return AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_status(request):
    """
    Get Kafka broker status and connection info.
    GET /api/integrations/kafka/status/

    Requires: kafka_access permission or SuperAdmin role
    """
    try:
        admin_client = get_admin_client()

        # Get cluster metadata
        metadata = admin_client.list_topics(timeout=5)

        broker_count = len(metadata.brokers)
        topic_count = len(metadata.topics)

        # Get broker info
        brokers = []
        for broker_id, broker_metadata in metadata.brokers.items():
            brokers.append({
                'id': broker_id,
                'host': broker_metadata.host,
                'port': broker_metadata.port
            })

        return Response({
            'status': 'connected',
            'broker': KAFKA_BOOTSTRAP_SERVERS,
            'brokerCount': broker_count,
            'topicCount': topic_count,
            'brokers': brokers,
            'clusterId': f'cluster-{broker_count}-brokers'
        })

    except KafkaException as e:
        logger.error(f"Kafka connection error: {str(e)}")
        return Response({
            'status': 'disconnected',
            'error': 'Unable to connect to Kafka broker',
            'broker': KAFKA_BOOTSTRAP_SERVERS,
            'details': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as e:
        logger.error(f"Error getting Kafka status: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_topics(request):
    """
    List all Kafka topics in the ContractAI event bus.
    GET /api/integrations/kafka/topics/

    Requires: kafka_access permission or SuperAdmin role
    """
    try:
        admin_client = get_admin_client()

        # Get cluster metadata
        metadata = admin_client.list_topics(timeout=5)

        topics_list = []
        for topic_name, topic_metadata in metadata.topics.items():
            # Skip internal topics
            if topic_name.startswith('__'):
                continue

            partition_count = len(topic_metadata.partitions)

            # Determine topic type based on naming convention
            topic_type = 'event'
            if 'request' in topic_name:
                topic_type = 'command'

            topics_list.append({
                'name': topic_name,
                'type': topic_type,
                'partitions': partition_count,
                'replicationFactor': 1,  # Default
                'description': _get_topic_description(topic_name)
            })

        return Response({
            'topics': topics_list,
            'total': len(topics_list)
        })

    except KafkaException as e:
        logger.error(f"Error listing topics: {str(e)}")
        return Response({
            'error': 'Failed to list Kafka topics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error in kafka_topics: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_publish(request):
    """
    Publish a message to a Kafka topic.
    POST /api/integrations/kafka/publish/

    Requires: kafka_access permission or SuperAdmin role

    Body:
    {
        "topic": "contract.review.request",
        "payload": {
            "contractId": "contract-uuid",
            "requestedBy": "user@example.com",
            "action": "FULL_REVIEW"
        }
    }
    """
    topic = request.data.get('topic')
    payload = request.data.get('payload')

    if not topic or not payload:
        return Response({
            'error': 'Both topic and payload are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from integrations.kafka.producer import publish_event

        # Add event_type if not present
        if 'event_type' not in payload:
            payload['event_type'] = topic.replace('.', '_')

        # Publish the event
        success = publish_event(topic, payload)

        if success:
            return Response({
                'message': f'Message published to topic: {topic}',
                'status': 'success',
                'topic': topic
            })
        else:
            return Response({
                'error': 'Failed to publish message',
                'topic': topic
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error publishing to Kafka: {str(e)}")
        return Response({
            'error': 'Failed to publish message',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_consumer_groups(request):
    """
    List Kafka consumer groups.
    GET /api/integrations/kafka/consumer-groups/

    Requires: kafka_access permission or SuperAdmin role
    """
    try:
        admin_client = get_admin_client()

        # List consumer groups
        consumer_groups = admin_client.list_consumer_groups(timeout=5)

        groups_list = []
        for group in consumer_groups.valid:
            groups_list.append({
                'groupId': group.group_id,
                'status': 'stable',  # Default status
                'protocol': group.protocol if hasattr(group, 'protocol') else 'unknown',
                'members': 'N/A'  # Would need additional API call to get member count
            })

        # If no consumer groups are running, return predefined groups
        if not groups_list:
            groups_list = [
                {
                    'groupId': 'contract-ai-agents',
                    'status': 'not_running',
                    'description': 'AI agent orchestrator consumer group'
                },
                {
                    'groupId': 'django-results',
                    'status': 'not_running',
                    'description': 'Django result processor consumer group'
                }
            ]

        return Response({
            'consumerGroups': groups_list,
            'total': len(groups_list)
        })

    except Exception as e:
        logger.error(f"Error listing consumer groups: {str(e)}")
        # Return mock data if Kafka is not available
        return Response({
            'consumerGroups': [
                {
                    'groupId': 'contract-ai-agents',
                    'status': 'unknown',
                    'description': 'AI agent orchestrator (status unavailable)'
                },
                {
                    'groupId': 'django-results',
                    'status': 'unknown',
                    'description': 'Django results processor (status unavailable)'
                }
            ],
            'note': 'Unable to fetch real-time consumer group data',
            'error': str(e)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_metrics(request):
    """
    Get Kafka metrics and monitoring data.
    GET /api/integrations/kafka/metrics/

    Requires: kafka_access permission or SuperAdmin role
    """
    try:
        admin_client = get_admin_client()
        metadata = admin_client.list_topics(timeout=5)

        # Count topics and partitions
        topic_count = len([t for t in metadata.topics.keys() if not t.startswith('__')])
        partition_count = sum(len(t.partitions) for t in metadata.topics.values())

        return Response({
            'metrics': {
                'broker': {
                    'status': 'healthy',
                    'brokerCount': len(metadata.brokers),
                    'bootstrap': KAFKA_BOOTSTRAP_SERVERS
                },
                'topics': {
                    'totalTopics': topic_count,
                    'totalPartitions': partition_count
                },
                'note': 'Detailed metrics require Kafka monitoring tools (JMX, Prometheus)'
            }
        })

    except Exception as e:
        logger.error(f"Error getting Kafka metrics: {str(e)}")
        return Response({
            'error': 'Failed to fetch Kafka metrics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_kafka_access
def kafka_create_topics(request):
    """
    Create Kafka topics for ContractAI.
    POST /api/integrations/kafka/create-topics/

    Requires: kafka_access permission or SuperAdmin role
    """
    try:
        admin_client = get_admin_client()

        # Define ContractAI topics
        topics_to_create = [
            NewTopic('contract.ingest', num_partitions=3, replication_factor=1),
            NewTopic('contract.review.request', num_partitions=3, replication_factor=1),
            NewTopic('contract.risk.request', num_partitions=3, replication_factor=1),
            NewTopic('contract.drift.request', num_partitions=3, replication_factor=1),
            NewTopic('contract.review.completed', num_partitions=3, replication_factor=1),
            NewTopic('contract.risk.scored', num_partitions=3, replication_factor=1),
            NewTopic('contract.drift.detected', num_partitions=3, replication_factor=1),
            NewTopic('contract.failed', num_partitions=3, replication_factor=1),
            NewTopic('integration.fivetran.sync', num_partitions=1, replication_factor=1),
        ]

        # Create topics
        fs = admin_client.create_topics(topics_to_create, operation_timeout=10)

        results = []
        for topic, f in fs.items():
            try:
                f.result()  # Wait for each operation to complete
                results.append({'topic': topic, 'status': 'created'})
            except KafkaException as e:
                if e.args[0].code() == -152:  # Topic already exists
                    results.append({'topic': topic, 'status': 'already_exists'})
                else:
                    results.append({'topic': topic, 'status': 'failed', 'error': str(e)})

        return Response({
            'message': 'Topic creation completed',
            'results': results
        })

    except Exception as e:
        logger.error(f"Error creating topics: {str(e)}")
        return Response({
            'error': 'Failed to create topics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_topic_description(topic_name: str) -> str:
    """Get human-readable description for a topic."""
    descriptions = {
        'contract.ingest': 'Contract ingestion events',
        'contract.review.request': 'Contract review requests',
        'contract.risk.request': 'Risk analysis requests',
        'contract.drift.request': 'Drift detection requests',
        'contract.review.completed': 'Completed contract reviews',
        'contract.risk.scored': 'Risk scoring results',
        'contract.drift.detected': 'Contract drift detection events',
        'contract.failed': 'Failed processing events',
        'integration.fivetran.sync': 'Fivetran sync completion events'
    }
    return descriptions.get(topic_name, 'Custom topic')
