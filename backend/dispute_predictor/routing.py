"""
WebSocket URL Routing for Dispute Predictor
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dispute-risk/$', consumers.DisputeRiskConsumer.as_asgi()),
]
