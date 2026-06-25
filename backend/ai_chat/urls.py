"""
AI Chat Assistant URL Routes
=============================
"""

from django.urls import path
from . import views

urlpatterns = [
    path('message', views.chat_message, name='chat_message'),
    path('history/<str:session_id>', views.chat_history, name='chat_history'),
    path('session/<str:session_id>', views.clear_session, name='clear_session'),
]
