"""
WebSocket consumers for real-time features in Koroh Platform.

This module provides WebSocket consumers for AI chat, notifications,
peer group activities, and dashboard updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from asgiref.sync import sync_to_async

logger = logging.getLogger('koroh_platform')


class BaseConsumer(AsyncWebsocketConsumer):
    """Base consumer with common functionality."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        
        # Allow anonymous users for certain consumers
        if self.user.is_anonymous and not self.allow_anonymous:
            await self.close()
            return
        
        await self.accept()
        await self.on_connect()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.on_disconnect(close_code)
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            await self.handle_message(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error("Internal server error")
    
    async def send_message(self, message_type, data):
        """Send a message to the WebSocket."""
        await self.send(text_data=json.dumps({
            'type': message_type,
            'data': data,
            'timestamp': self.get_timestamp()
        }, cls=DjangoJSONEncoder))
    
    async def send_error(self, error_message):
        """Send an error message to the WebSocket."""
        await self.send_message('error', {'message': error_message})
    
    def get_timestamp(self):
        """Get current timestamp."""
        from django.utils import timezone
        return timezone.now().isoformat()
    
    # Override these methods in subclasses
    allow_anonymous = False
    
    async def on_connect(self):
        """Called after successful connection."""
        pass
    
    async def on_disconnect(self, close_code):
        """Called on disconnection."""
        pass
    
    async def handle_message(self, data):
        """Handle incoming messages."""
        pass


class AIChatConsumer(BaseConsumer):
    """WebSocket consumer for AI chat real-time messaging."""
    
    allow_anonymous = True  # Allow anonymous chat
    
    async def on_connect(self):
        """Handle AI chat connection."""
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        
        if self.user.is_authenticated:
            # Authenticated user - join personal chat room
            self.room_group_name = f'ai_chat_user_{self.user.id}'
        else:
            # Anonymous user - use session-based room
            session_key = self.scope.get('session', {}).get('session_key')
            if not session_key:
                # Generate a temporary session key for anonymous users
                import uuid
                session_key = str(uuid.uuid4())
            self.room_group_name = f'ai_chat_anonymous_{session_key}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send connection confirmation
        await self.send_message('connected', {
            'session_id': self.session_id,
            'is_authenticated': self.user.is_authenticated,
            'room': self.room_group_name
        })
    
    async def on_disconnect(self, close_code):
        """Handle AI chat disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def handle_message(self, data):
        """Handle AI chat messages."""
        message_type = data.get('type')
        
        if message_type == 'send_message':
            await self.handle_send_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'stop_typing':
            await self.handle_stop_typing(data)
    
    async def handle_send_message(self, data):
        """Handle sending a message to AI."""
        message = data.get('message', '').strip()
        if not message:
            await self.send_error("Message cannot be empty")
            return
        
        try:
            # Process AI message (this would typically be done via Celery)
            if self.user.is_authenticated:
                result = await self.process_authenticated_message(message)
            else:
                result = await self.process_anonymous_message(message)
            
            # Send the result back to the user
            await self.send_message('message_response', result)
            
        except Exception as e:
            logger.error(f"Error processing AI message: {e}")
            await self.send_error("Failed to process message")
    
    async def handle_typing(self, data):
        """Handle typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id if self.user.is_authenticated else None,
                'is_typing': True
            }
        )
    
    async def handle_stop_typing(self, data):
        """Handle stop typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id if self.user.is_authenticated else None,
                'is_typing': False
            }
        )
    
    @database_sync_to_async
    def process_authenticated_message(self, message):
        """Process message for authenticated user."""
        from ai_chat.services import ChatService
        
        chat_service = ChatService()
        user_message, ai_message = chat_service.send_message(
            user=self.user,
            message=message,
            session_id=self.session_id
        )
        
        return {
            'session_id': str(user_message.session.id),
            'user_message': {
                'id': str(user_message.id),
                'content': user_message.content,
                'timestamp': user_message.created_at.isoformat()
            },
            'ai_response': {
                'id': str(ai_message.id),
                'content': ai_message.content,
                'timestamp': ai_message.created_at.isoformat()
            }
        }
    
    @database_sync_to_async
    def process_anonymous_message(self, message):
        """Process message for anonymous user."""
        from ai_chat.services import AnonymousChatService
        
        session_key = self.scope.get('session', {}).get('session_key')
        ip_address = self.get_client_ip()
        
        chat_service = AnonymousChatService()
        user_message, ai_message = chat_service.send_anonymous_message(
            session_key=session_key,
            ip_address=ip_address,
            message=message
        )
        
        # Check remaining messages
        from ai_chat.models import AnonymousChatLimit
        limit = AnonymousChatLimit.objects.filter(
            session_key=session_key,
            ip_address=ip_address
        ).first()
        
        messages_remaining = 5 - (limit.message_count if limit else 0)
        
        return {
            'session_id': str(user_message.session.id),
            'user_message': {
                'id': str(user_message.id),
                'content': user_message.content,
                'timestamp': user_message.created_at.isoformat()
            },
            'ai_response': {
                'id': str(ai_message.id),
                'content': ai_message.content,
                'timestamp': ai_message.created_at.isoformat()
            },
            'messages_remaining': messages_remaining,
            'registration_prompt': messages_remaining <= 1
        }
    
    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.scope.get('headers', {}).get(b'x-forwarded-for')
        if x_forwarded_for:
            return x_forwarded_for.decode('utf-8').split(',')[0]
        return self.scope.get('client', ['unknown'])[0]
    
    # WebSocket message handlers
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        await self.send_message('typing', {
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        })


class NotificationConsumer(BaseConsumer):
    """WebSocket consumer for real-time notifications."""
    
    async def on_connect(self):
        """Handle notification connection."""
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_group_name = f'notifications_user_{self.user.id}'
        
        # Join notification room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send recent notifications
        await self.send_recent_notifications()
    
    async def on_disconnect(self, close_code):
        """Handle notification disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def handle_message(self, data):
        """Handle notification-related messages."""
        message_type = data.get('type')
        
        if message_type == 'mark_read':
            await self.handle_mark_read(data)
        elif message_type == 'get_notifications':
            await self.send_recent_notifications()
    
    async def handle_mark_read(self, data):
        """Mark notifications as read."""
        notification_ids = data.get('notification_ids', [])
        if notification_ids:
            await self.mark_notifications_read(notification_ids)
    
    @database_sync_to_async
    def send_recent_notifications(self):
        """Send recent notifications to the user."""
        # This would fetch recent notifications from the database
        # For now, we'll send a placeholder
        notifications = []
        return self.send_message('notifications', {
            'notifications': notifications,
            'unread_count': 0
        })
    
    @database_sync_to_async
    def mark_notifications_read(self, notification_ids):
        """Mark notifications as read in the database."""
        # Implementation would update notification read status
        pass
    
    # WebSocket message handlers
    async def new_notification(self, event):
        """Send new notification to WebSocket."""
        await self.send_message('new_notification', event['notification'])
    
    async def notification_update(self, event):
        """Send notification update to WebSocket."""
        await self.send_message('notification_update', event['update'])


class PeerGroupConsumer(BaseConsumer):
    """WebSocket consumer for peer group real-time activities."""
    
    async def on_connect(self):
        """Handle peer group connection."""
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.group_slug = self.scope['url_route']['kwargs']['group_slug']
        self.room_group_name = f'peer_group_{self.group_slug}'
        
        # Check if user is a member of the group
        is_member = await self.check_group_membership()
        if not is_member:
            await self.close()
            return
        
        # Join group room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send connection confirmation
        await self.send_message('connected', {
            'group_slug': self.group_slug,
            'user_id': self.user.id
        })
    
    async def on_disconnect(self, close_code):
        """Handle peer group disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def handle_message(self, data):
        """Handle peer group messages."""
        message_type = data.get('type')
        
        if message_type == 'get_activity':
            await self.send_group_activity()
        elif message_type == 'user_typing':
            await self.handle_user_typing(data)
    
    async def handle_user_typing(self, data):
        """Handle user typing in group."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': data.get('is_typing', False)
            }
        )
    
    @database_sync_to_async
    def check_group_membership(self):
        """Check if user is a member of the group."""
        from peer_groups.models import PeerGroup
        try:
            group = PeerGroup.objects.get(slug=self.group_slug)
            return group.is_member(self.user)
        except PeerGroup.DoesNotExist:
            return False
    
    @database_sync_to_async
    def send_group_activity(self):
        """Send recent group activity."""
        # This would fetch recent activity from the database
        activity = []
        return self.send_message('activity', {
            'activity': activity,
            'group_slug': self.group_slug
        })
    
    # WebSocket message handlers
    async def new_post(self, event):
        """Send new post notification to WebSocket."""
        await self.send_message('new_post', event['post'])
    
    async def new_comment(self, event):
        """Send new comment notification to WebSocket."""
        await self.send_message('new_comment', event['comment'])
    
    async def member_joined(self, event):
        """Send member joined notification to WebSocket."""
        await self.send_message('member_joined', event['member'])
    
    async def user_typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator back to the same user
        if event['user_id'] != self.user.id:
            await self.send_message('user_typing', {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            })


class PeerGroupActivityConsumer(BaseConsumer):
    """WebSocket consumer for global peer group activity feed."""
    
    async def on_connect(self):
        """Handle activity feed connection."""
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_group_name = f'peer_group_activity_user_{self.user.id}'
        
        # Join activity room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send recent activity
        await self.send_user_activity_feed()
    
    async def on_disconnect(self, close_code):
        """Handle activity feed disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def handle_message(self, data):
        """Handle activity feed messages."""
        message_type = data.get('type')
        
        if message_type == 'get_activity':
            await self.send_user_activity_feed()
    
    @database_sync_to_async
    def send_user_activity_feed(self):
        """Send user's activity feed."""
        # This would fetch activity from user's groups
        activity = []
        return self.send_message('activity_feed', {
            'activity': activity,
            'user_id': self.user.id
        })
    
    # WebSocket message handlers
    async def activity_update(self, event):
        """Send activity update to WebSocket."""
        await self.send_message('activity_update', event['activity'])


class DashboardConsumer(BaseConsumer):
    """WebSocket consumer for dashboard real-time updates."""
    
    async def on_connect(self):
        """Handle dashboard connection."""
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_group_name = f'dashboard_user_{self.user.id}'
        
        # Join dashboard room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send initial dashboard data
        await self.send_dashboard_data()
    
    async def on_disconnect(self, close_code):
        """Handle dashboard disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def handle_message(self, data):
        """Handle dashboard messages."""
        message_type = data.get('type')
        
        if message_type == 'refresh_data':
            await self.send_dashboard_data()
    
    @database_sync_to_async
    def send_dashboard_data(self):
        """Send dashboard data."""
        # This would fetch dashboard data from various sources
        dashboard_data = {
            'job_recommendations': [],
            'company_updates': [],
            'peer_group_activity': [],
            'notifications': []
        }
        return self.send_message('dashboard_data', dashboard_data)
    
    # WebSocket message handlers
    async def job_recommendation_update(self, event):
        """Send job recommendation update to WebSocket."""
        await self.send_message('job_recommendation_update', event['recommendation'])
    
    async def company_update(self, event):
        """Send company update to WebSocket."""
        await self.send_message('company_update', event['update'])
    
    async def dashboard_refresh(self, event):
        """Send dashboard refresh signal to WebSocket."""
        await self.send_message('dashboard_refresh', event['data'])