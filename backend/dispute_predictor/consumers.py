"""
WebSocket Consumer for Real-Time Dispute Risk Updates
======================================================
Sends live risk updates to connected clients when:
- New predictions are made
- Risk scores change
- Bayesian network updates occur
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DisputePrediction, DisputeRiskNode

logger = logging.getLogger(__name__)


class DisputeRiskConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dispute risk updates.

    Channel: /ws/dispute-risk/

    Receives: -
    Sends:
        - risk_update: Updated risk probabilities for nodes
        - prediction_complete: New prediction results
        - graph_update: Graph structure changes
    """

    async def connect(self):
        """Accept WebSocket connection and join dispute risk group."""
        self.room_group_name = 'dispute_risk_updates'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")

        # Send initial graph data on connect
        await self.send_initial_graph()

    async def disconnect(self, close_code):
        """Leave room group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name} (code: {close_code})")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))

            elif message_type == 'subscribe_predictions':
                # Client wants to subscribe to prediction updates
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'channel': 'predictions'
                }))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error in receive: {e}")

    async def send_initial_graph(self):
        """Send initial risk graph data to newly connected client."""
        try:
            graph_data = await self.get_graph_data()
            await self.send(text_data=json.dumps({
                'type': 'initial_graph',
                'data': graph_data
            }))
        except Exception as e:
            logger.error(f"Error sending initial graph: {e}")

    async def risk_update(self, event):
        """
        Handler for risk_update events from channel layer.

        Event format:
        {
            'type': 'risk_update',
            'node_id': 'war_risk',
            'old_probability': 0.05,
            'new_probability': 0.15,
            'affected_nodes': ['commodity_price_volatility', ...]
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'risk_update',
            'node_id': event['node_id'],
            'old_probability': event.get('old_probability'),
            'new_probability': event['new_probability'],
            'affected_nodes': event.get('affected_nodes', []),
            'timestamp': event.get('timestamp')
        }))

    async def prediction_complete(self, event):
        """
        Handler for prediction_complete events.

        Event format:
        {
            'type': 'prediction_complete',
            'prediction_id': '123',
            'dispute_probability': 0.68,
            'contract_risk': 0.72,
            'top_drivers': [...]
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'prediction_complete',
            'prediction_id': event['prediction_id'],
            'dispute_probability': event['dispute_probability'],
            'arbitration_probability': event.get('arbitration_probability'),
            'contract_risk': event.get('contract_risk'),
            'top_drivers': event.get('top_drivers', []),
            'timestamp': event.get('timestamp')
        }))

    async def graph_update(self, event):
        """
        Handler for graph structure updates.

        Event format:
        {
            'type': 'graph_update',
            'nodes': [...],
            'edges': [...]
        }
        """
        await self.send(text_data=json.dumps({
            'type': 'graph_update',
            'nodes': event.get('nodes', []),
            'edges': event.get('edges', []),
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_graph_data(self):
        """Fetch current risk graph data from database."""
        nodes = DisputeRiskNode.objects.all().values(
            'id', 'node_id', 'label', 'cluster', 'layer', 'base_probability'
        )

        # For simplicity, we'll fetch edges from the DisputeRiskEdge model
        from .models import DisputeRiskEdge
        edges = DisputeRiskEdge.objects.all().values(
            'source_node_id', 'target_node_id', 'conditional_probability'
        )

        return {
            'nodes': list(nodes),
            'edges': list(edges)
        }


# Utility function to broadcast risk updates
async def broadcast_risk_update(channel_layer, node_id, old_prob, new_prob, affected_nodes=None):
    """
    Broadcast risk update to all connected WebSocket clients.

    Usage:
        from channels.layers import get_channel_layer
        from dispute_predictor.consumers import broadcast_risk_update

        channel_layer = get_channel_layer()
        await broadcast_risk_update(
            channel_layer,
            node_id='war_risk',
            old_prob=0.05,
            new_prob=0.15,
            affected_nodes=['commodity_price_volatility']
        )
    """
    import time
    await channel_layer.group_send(
        'dispute_risk_updates',
        {
            'type': 'risk_update',
            'node_id': node_id,
            'old_probability': old_prob,
            'new_probability': new_prob,
            'affected_nodes': affected_nodes or [],
            'timestamp': time.time()
        }
    )


async def broadcast_prediction_complete(channel_layer, prediction_data):
    """
    Broadcast prediction completion to all connected clients.

    Usage:
        await broadcast_prediction_complete(
            channel_layer,
            {
                'prediction_id': '123',
                'dispute_probability': 0.68,
                'contract_risk': 0.72,
                'top_drivers': [...]
            }
        )
    """
    import time
    await channel_layer.group_send(
        'dispute_risk_updates',
        {
            'type': 'prediction_complete',
            **prediction_data,
            'timestamp': time.time()
        }
    )
