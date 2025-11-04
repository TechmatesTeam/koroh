"""
AI Chat Views for Koroh Platform

This module provides REST API endpoints for AI chat functionality,
including message sending, session management, and platform integration.
"""

import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, 
    ChatSessionListSerializer,
    ChatMessageSerializer,
    SendMessageSerializer
)
from .services import ChatService, PlatformIntegrationService, AnonymousChatService
from koroh_platform.permissions import (
    AIServicePermission,
    IsOwnerOrReadOnly,
    IsAnonymousOrAuthenticated,
    log_permission_denied
)

logger = logging.getLogger('koroh_platform.security')


class ChatSessionListView(APIView):
    """
    List user's chat sessions or create a new one.
    """
    permission_classes = [AIServicePermission]
    
    def get(self, request):
        """Get list of user's chat sessions."""
        try:
            chat_service = ChatService()
            sessions = chat_service.list_user_sessions(request.user)
            serializer = ChatSessionListSerializer(sessions, many=True)
            
            return Response({
                'sessions': serializer.data,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            logger.error(f"Error listing chat sessions for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to retrieve chat sessions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Create a new chat session."""
        try:
            chat_service = ChatService()
            session = chat_service.get_or_create_session(request.user)
            serializer = ChatSessionSerializer(session)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating chat session for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to create chat session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatSessionDetailView(APIView):
    """
    Retrieve, update, or delete a specific chat session.
    """
    permission_classes = [IsOwnerOrReadOnly]
    
    def get(self, request, session_id):
        """Get chat session with message history."""
        try:
            chat_service = ChatService()
            session = chat_service.get_session_history(request.user, session_id)
            
            if not session:
                return Response(
                    {'error': 'Chat session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = ChatSessionSerializer(session)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error retrieving chat session {session_id}: {e}")
            return Response(
                {'error': 'Failed to retrieve chat session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, session_id):
        """Update chat session (e.g., title)."""
        try:
            session = get_object_or_404(
                ChatSession, 
                id=session_id, 
                user=request.user, 
                is_active=True
            )
            
            # Only allow updating title for now
            if 'title' in request.data:
                session.title = request.data['title']
                session.save()
            
            serializer = ChatSessionSerializer(session)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating chat session {session_id}: {e}")
            return Response(
                {'error': 'Failed to update chat session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, session_id):
        """Delete (deactivate) chat session."""
        try:
            chat_service = ChatService()
            success = chat_service.delete_session(request.user, session_id)
            
            if not success:
                return Response(
                    {'error': 'Chat session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({'message': 'Chat session deleted successfully'})
            
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {e}")
            return Response(
                {'error': 'Failed to delete chat session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SendMessageView(APIView):
    """
    Send a message to the AI chat and get a response.
    """
    permission_classes = [AIServicePermission]
    
    def post(self, request):
        """Send message and get AI response."""
        try:
            serializer = SendMessageSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            message = serializer.validated_data['message']
            session_id = serializer.validated_data.get('session_id')
            additional_context = serializer.validated_data.get('context', {})
            
            chat_service = ChatService()
            user_message, ai_message = chat_service.send_message(
                user=request.user,
                message=message,
                session_id=session_id,
                additional_context=additional_context
            )
            
            return Response({
                'session_id': str(user_message.session.id),
                'user_message': ChatMessageSerializer(user_message).data,
                'ai_response': ChatMessageSerializer(ai_message).data
            })
            
        except Exception as e:
            logger.error(f"Error processing chat message for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to process message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([AIServicePermission])
def quick_chat(request):
    """
    Quick chat endpoint for single message/response without session management.
    Useful for simple AI assistance without maintaining conversation history.
    """
    try:
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chat_service = ChatService()
        user_message, ai_message = chat_service.send_message(
            user=request.user,
            message=message
        )
        
        return Response({
            'message': message,
            'response': ai_message.content,
            'session_id': str(ai_message.session.id)
        })
        
    except Exception as e:
        logger.error(f"Error in quick chat for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to process quick chat'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAnonymousOrAuthenticated])
def anonymous_chat(request):
    """
    Anonymous chat endpoint with message limits.
    Allows up to 5 messages for non-registered users.
    """
    try:
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get session key and IP address for anonymous tracking
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        ip_address = get_client_ip(request)
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Redirect to regular chat for authenticated users
            chat_service = ChatService()
            user_message, ai_message = chat_service.send_message(
                user=request.user,
                message=message
            )
            
            return Response({
                'message': message,
                'response': ai_message.content,
                'session_id': str(ai_message.session.id),
                'is_authenticated': True,
                'messages_remaining': None
            })
        
        # Check anonymous user limits
        from .models import AnonymousChatLimit
        max_messages = 5
        
        if AnonymousChatLimit.check_limit_exceeded(session_key, ip_address, max_messages):
            return Response({
                'error': 'Message limit exceeded',
                'message': f'You have reached the maximum of {max_messages} messages. Please register to continue chatting.',
                'limit_exceeded': True,
                'max_messages': max_messages,
                'registration_required': True
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Process anonymous chat
        chat_service = AnonymousChatService()
        user_message, ai_message = chat_service.send_anonymous_message(
            session_key=session_key,
            ip_address=ip_address,
            message=message
        )
        
        # Increment message count
        limit = AnonymousChatLimit.increment_count(session_key, ip_address)
        messages_remaining = max_messages - limit.message_count
        
        return Response({
            'message': message,
            'response': ai_message.content,
            'session_id': str(ai_message.session.id),
            'is_authenticated': False,
            'messages_remaining': messages_remaining,
            'max_messages': max_messages,
            'registration_prompt': messages_remaining <= 1
        })
        
    except Exception as e:
        logger.error(f"Error in anonymous chat: {e}")
        return Response(
            {'error': 'Failed to process message'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AIServicePermission])
def analyze_cv_chat(request):
    """
    Chat endpoint specifically for CV analysis requests.
    """
    try:
        session_id = request.data.get('session_id')
        
        integration_service = PlatformIntegrationService()
        result = integration_service.handle_cv_analysis_request(request.user, session_id)
        
        if result['success']:
            # Send the analysis result as a chat message
            chat_service = ChatService()
            user_message, ai_message = chat_service.send_message(
                user=request.user,
                message="Please analyze my CV",
                session_id=session_id,
                additional_context={'cv_analysis_result': result['data']}
            )
            
            return Response({
                'session_id': str(user_message.session.id),
                'analysis_result': result,
                'ai_response': ChatMessageSerializer(ai_message).data
            })
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in CV analysis chat for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to analyze CV'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AIServicePermission])
def generate_portfolio_chat(request):
    """
    Chat endpoint specifically for portfolio generation requests.
    """
    try:
        session_id = request.data.get('session_id')
        
        integration_service = PlatformIntegrationService()
        result = integration_service.handle_portfolio_generation_request(request.user, session_id)
        
        # Send the portfolio generation result as a chat message
        chat_service = ChatService()
        user_message, ai_message = chat_service.send_message(
            user=request.user,
            message="Help me generate a portfolio",
            session_id=session_id,
            additional_context={'portfolio_generation_result': result}
        )
        
        return Response({
            'session_id': str(user_message.session.id),
            'generation_result': result,
            'ai_response': ChatMessageSerializer(ai_message).data
        })
        
    except Exception as e:
        logger.error(f"Error in portfolio generation chat for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to generate portfolio'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AIServicePermission])
def job_recommendations_chat(request):
    """
    Chat endpoint specifically for job recommendation requests.
    """
    try:
        session_id = request.data.get('session_id')
        
        integration_service = PlatformIntegrationService()
        result = integration_service.handle_job_recommendations_request(request.user, session_id)
        
        # Send the job recommendations as a chat message
        chat_service = ChatService()
        user_message, ai_message = chat_service.send_message(
            user=request.user,
            message="Show me job recommendations",
            session_id=session_id,
            additional_context={'job_recommendations_result': result}
        )
        
        return Response({
            'session_id': str(user_message.session.id),
            'recommendations_result': result,
            'ai_response': ChatMessageSerializer(ai_message).data
        })
        
    except Exception as e:
        logger.error(f"Error in job recommendations chat for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to get job recommendations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AIServicePermission])
def get_conversation_context(request, session_id):
    """
    Get conversation context information for a chat session.
    """
    try:
        session = get_object_or_404(
            ChatSession, 
            id=session_id, 
            user=request.user, 
            is_active=True
        )
        
        context_data = {}
        if hasattr(session, 'context'):
            context = session.context
            context_data = {
                'conversation_stage': context.conversation_stage,
                'active_topics': [t.get('topic') for t in (context.conversation_topics or [])[-5:]],
                'recent_intents': [i.get('intent') for i in (context.user_intent_history or [])[-3:]],
                'key_entities': {
                    entity_type: [e.get('value') for e in entities[-3:]]
                    for entity_type, entities in (context.mentioned_entities or {}).items()
                },
                'user_goals': context.conversation_goals or [],
                'key_insights': [i.get('insight') for i in (context.key_insights or [])[-3:]],
                'context_confidence': context.context_confidence,
                'active_features': context.active_features or [],
                'conversation_summary': context.conversation_summary,
                'context_version': context.context_version
            }
        
        return Response({
            'session_id': str(session.id),
            'message_count': session.messages.count(),
            'context': context_data
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation context for session {session_id}: {e}")
        return Response(
            {'error': 'Failed to get conversation context'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )