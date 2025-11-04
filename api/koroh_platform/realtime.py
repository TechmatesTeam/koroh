"""
Real-time notification and update services for Koroh Platform.

This module provides services for sending real-time updates via WebSockets
for various platform features including AI chat, peer groups, and notifications.
"""

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger('koroh_platform')


class RealtimeService:
    """Base service for real-time WebSocket communications."""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_to_group(self, group_name, message_type, data):
        """Send a message to a WebSocket group."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping real-time message")
            return
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
        except Exception as e:
            logger.error(f"Failed to send real-time message to group {group_name}: {e}")
    
    def send_to_user(self, user_id, message_type, data):
        """Send a message to a specific user."""
        group_name = f"notifications_user_{user_id}"
        self.send_to_group(group_name, message_type, data)


class NotificationRealtimeService(RealtimeService):
    """Service for real-time notifications."""
    
    def send_notification(self, user_id, notification_data):
        """Send a new notification to a user."""
        self.send_to_user(user_id, 'new_notification', {
            'notification': notification_data
        })
    
    def send_notification_update(self, user_id, update_data):
        """Send a notification update to a user."""
        self.send_to_user(user_id, 'notification_update', {
            'update': update_data
        })
    
    def broadcast_system_notification(self, notification_data):
        """Broadcast a system notification to all connected users."""
        # This would require tracking all connected users
        # For now, we'll implement user-specific notifications
        pass


class PeerGroupRealtimeService(RealtimeService):
    """Service for real-time peer group updates."""
    
    def send_new_post(self, group_slug, post_data):
        """Send new post notification to group members."""
        group_name = f"peer_group_{group_slug}"
        self.send_to_group(group_name, 'new_post', {
            'post': post_data
        })
    
    def send_new_comment(self, group_slug, comment_data):
        """Send new comment notification to group members."""
        group_name = f"peer_group_{group_slug}"
        self.send_to_group(group_name, 'new_comment', {
            'comment': comment_data
        })
    
    def send_member_joined(self, group_slug, member_data):
        """Send member joined notification to group members."""
        group_name = f"peer_group_{group_slug}"
        self.send_to_group(group_name, 'member_joined', {
            'member': member_data
        })
    
    def send_activity_update(self, user_id, activity_data):
        """Send activity update to user's activity feed."""
        group_name = f"peer_group_activity_user_{user_id}"
        self.send_to_group(group_name, 'activity_update', {
            'activity': activity_data
        })


class DashboardRealtimeService(RealtimeService):
    """Service for real-time dashboard updates."""
    
    def send_job_recommendation_update(self, user_id, recommendation_data):
        """Send job recommendation update to user's dashboard."""
        group_name = f"dashboard_user_{user_id}"
        self.send_to_group(group_name, 'job_recommendation_update', {
            'recommendation': recommendation_data
        })
    
    def send_company_update(self, user_id, company_data):
        """Send company update to user's dashboard."""
        group_name = f"dashboard_user_{user_id}"
        self.send_to_group(group_name, 'company_update', {
            'update': company_data
        })
    
    def send_dashboard_refresh(self, user_id, refresh_data=None):
        """Send dashboard refresh signal to user."""
        group_name = f"dashboard_user_{user_id}"
        self.send_to_group(group_name, 'dashboard_refresh', {
            'data': refresh_data or {}
        })


class AIChatRealtimeService(RealtimeService):
    """Service for real-time AI chat updates."""
    
    def send_ai_response_stream(self, user_id, session_id, response_chunk):
        """Send streaming AI response to user."""
        if user_id:
            group_name = f"ai_chat_user_{user_id}"
        else:
            # Anonymous user - would need session key
            return
        
        self.send_to_group(group_name, 'ai_response_stream', {
            'session_id': session_id,
            'chunk': response_chunk
        })
    
    def send_ai_response_complete(self, user_id, session_id, complete_response):
        """Send complete AI response to user."""
        if user_id:
            group_name = f"ai_chat_user_{user_id}"
        else:
            return
        
        self.send_to_group(group_name, 'ai_response_complete', {
            'session_id': session_id,
            'response': complete_response
        })


# Global service instances
notification_service = NotificationRealtimeService()
peer_group_service = PeerGroupRealtimeService()
dashboard_service = DashboardRealtimeService()
ai_chat_service = AIChatRealtimeService()


# Convenience functions for easy access
def send_notification(user_id, notification_data):
    """Send a real-time notification to a user."""
    notification_service.send_notification(user_id, notification_data)


def send_peer_group_update(group_slug, update_type, data):
    """Send a real-time update to a peer group."""
    if update_type == 'new_post':
        peer_group_service.send_new_post(group_slug, data)
    elif update_type == 'new_comment':
        peer_group_service.send_new_comment(group_slug, data)
    elif update_type == 'member_joined':
        peer_group_service.send_member_joined(group_slug, data)


def send_dashboard_update(user_id, update_type, data):
    """Send a real-time update to a user's dashboard."""
    if update_type == 'job_recommendation':
        dashboard_service.send_job_recommendation_update(user_id, data)
    elif update_type == 'company_update':
        dashboard_service.send_company_update(user_id, data)
    elif update_type == 'refresh':
        dashboard_service.send_dashboard_refresh(user_id, data)


def send_ai_chat_update(user_id, session_id, update_type, data):
    """Send a real-time update to AI chat."""
    if update_type == 'response_stream':
        ai_chat_service.send_ai_response_stream(user_id, session_id, data)
    elif update_type == 'response_complete':
        ai_chat_service.send_ai_response_complete(user_id, session_id, data)