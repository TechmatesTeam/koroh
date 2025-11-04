"""
WebSocket URL routing for Koroh Platform.

This module defines WebSocket URL patterns for real-time features
including AI chat, notifications, and peer group activity feeds.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # AI Chat WebSocket
    path('ws/ai-chat/', consumers.AIChatConsumer.as_asgi()),
    path('ws/ai-chat/<str:session_id>/', consumers.AIChatConsumer.as_asgi()),
    
    # Notifications WebSocket
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    
    # Peer Groups WebSocket
    path('ws/peer-groups/<str:group_slug>/', consumers.PeerGroupConsumer.as_asgi()),
    path('ws/peer-groups/activity/', consumers.PeerGroupActivityConsumer.as_asgi()),
    
    # Dashboard WebSocket for real-time updates
    path('ws/dashboard/', consumers.DashboardConsumer.as_asgi()),
]