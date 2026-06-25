"""
WebSocket URL Routing for Negotiation
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/negotiation/(?P<session_id>[\w-]+)/$', consumers.NegotiationConsumer.as_asgi()),
]
