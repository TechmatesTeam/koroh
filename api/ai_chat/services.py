"""
AI Chat Services for Koroh Platform

This module provides services for managing AI chat conversations,
including context management, message processing, and integration
with platform features.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.contrib.auth import get_user_model
from django.utils import timezone
from koroh_platform.utils.ai_services import AIServiceFactory, ConversationalAIService
from .models import ChatSession, ChatMessage, ChatContext, AnonymousChatLimit

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing AI chat conversations and context.
    """
    
    def __init__(self):
        self.ai_service = AIServiceFactory.create_conversational_service()
    
    def get_or_create_session(self, user: User, session_id: Optional[str] = None) -> ChatSession:
        """
        Get existing session or create a new one.
        
        Args:
            user: The user requesting the session
            session_id: Optional existing session ID
            
        Returns:
            ChatSession instance
        """
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=user, is_active=True)
                return session
            except ChatSession.DoesNotExist:
                logger.warning(f"Session {session_id} not found for user {user.id}, creating new session")
        
        # Create new session
        session = ChatSession.objects.create(user=user)
        
        # Create context for the session
        ChatContext.objects.create(
            session=session,
            user_profile_data=self._get_user_profile_data(user)
        )
        
        logger.info(f"Created new chat session {session.id} for user {user.id}")
        return session
    
    def send_message(
        self, 
        user: User, 
        message: str, 
        session_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ChatMessage, ChatMessage]:
        """
        Send a message and get AI response.
        
        Args:
            user: The user sending the message
            message: The message content
            session_id: Optional session ID
            additional_context: Additional context for the conversation
            
        Returns:
            Tuple of (user_message, ai_response)
        """
        # Get or create session
        session = self.get_or_create_session(user, session_id)
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message,
            status='completed'
        )
        
        # Create AI response message (initially pending)
        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='',
            status='processing'
        )
        
        try:
            # Get conversation context
            context = self._build_conversation_context(session, additional_context)
            
            # Generate AI response
            ai_response = self._generate_ai_response(message, context)
            
            # Update AI message with response
            ai_message.content = ai_response
            ai_message.status = 'completed'
            ai_message.save()
            
            # Update session context
            self._update_session_context(session, message, ai_response, additional_context)
            
            # Update session timestamp
            session.updated_at = timezone.now()
            session.save()
            
            logger.info(f"Successfully processed message in session {session.id}")
            
        except Exception as e:
            logger.error(f"Error processing message in session {session.id}: {e}")
            ai_message.content = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
            ai_message.status = 'failed'
            ai_message.save()
        
        return user_message, ai_message
    
    def get_session_history(self, user: User, session_id: str) -> Optional[ChatSession]:
        """
        Get chat session with message history.
        
        Args:
            user: The user requesting the session
            session_id: Session ID
            
        Returns:
            ChatSession with messages or None if not found
        """
        try:
            return ChatSession.objects.prefetch_related('messages').get(
                id=session_id, 
                user=user, 
                is_active=True
            )
        except ChatSession.DoesNotExist:
            return None
    
    def list_user_sessions(self, user: User, limit: int = 20) -> List[ChatSession]:
        """
        List user's chat sessions.
        
        Args:
            user: The user
            limit: Maximum number of sessions to return
            
        Returns:
            List of ChatSession objects
        """
        return ChatSession.objects.filter(
            user=user, 
            is_active=True
        ).prefetch_related('messages')[:limit]
    
    def delete_session(self, user: User, session_id: str) -> bool:
        """
        Delete (deactivate) a chat session.
        
        Args:
            user: The user
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.is_active = False
            session.save()
            logger.info(f"Deactivated chat session {session_id} for user {user.id}")
            return True
        except ChatSession.DoesNotExist:
            return False
    
    def _get_user_profile_data(self, user: User) -> Dict[str, Any]:
        """Get user profile data for context."""
        try:
            profile = user.profile
            return {
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'headline': getattr(profile, 'headline', ''),
                'summary': getattr(profile, 'summary', ''),
                'location': getattr(profile, 'location', ''),
                'industry': getattr(profile, 'industry', ''),
                'experience_level': getattr(profile, 'experience_level', ''),
                'skills': getattr(profile, 'skills', []),
                'has_cv': bool(getattr(profile, 'cv_file', None)),
                'has_portfolio': bool(getattr(profile, 'portfolio_url', None))
            }
        except Exception as e:
            logger.warning(f"Could not get profile data for user {user.id}: {e}")
            return {
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'has_cv': False,
                'has_portfolio': False
            }
    
    def _build_conversation_context(
        self, 
        session: ChatSession, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build conversation context for AI service."""
        # Get recent messages for context
        recent_messages = session.messages.order_by('-created_at')[:10]
        context_messages = []
        
        for msg in reversed(recent_messages):
            context_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Get session context
        session_context = getattr(session, 'context', None)
        user_profile = session_context.user_profile_data if session_context else {}
        
        # Build full context
        context = {
            'user_profile': user_profile,
            'conversation_history': context_messages,
            'session_id': str(session.id),
            'platform_features': {
                'cv_upload': True,
                'portfolio_generation': True,
                'job_search': True,
                'company_discovery': True,
                'peer_groups': True
            }
        }
        
        # Add additional context if provided
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _generate_ai_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate AI response using the conversational service."""
        try:
            input_data = {
                'message': message,
                'context': context.get('conversation_history', []),
                'user_profile': context.get('user_profile', {})
            }
            
            response = self.ai_service.process(input_data)
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def _update_session_context(
        self, 
        session: ChatSession, 
        user_message: str, 
        ai_response: str,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Update session context based on the conversation."""
        try:
            context, created = ChatContext.objects.get_or_create(session=session)
            
            # Update conversation summary if needed (every 10 messages)
            message_count = session.messages.count()
            if message_count % 10 == 0:
                context.conversation_summary = self._generate_conversation_summary(session)
            
            # Detect active features being discussed
            active_features = self._detect_active_features(user_message, ai_response)
            if active_features:
                context.active_features = list(set(context.active_features + active_features))
            
            # Update context data
            if additional_context:
                context.context_data.update(additional_context)
            
            context.save()
            
        except Exception as e:
            logger.error(f"Error updating session context: {e}")
    
    def _generate_conversation_summary(self, session: ChatSession) -> str:
        """Generate a summary of the conversation for context."""
        try:
            recent_messages = session.messages.order_by('-created_at')[:20]
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in reversed(recent_messages)
            ])
            
            # Use AI to generate summary
            summary_input = {
                'message': f"Please provide a brief summary of this conversation:\n\n{conversation_text}",
                'context': [],
                'user_profile': {}
            }
            
            summary = self.ai_service.process(summary_input)
            return summary[:500]  # Limit summary length
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Conversation about career and professional development."
    
    def _detect_active_features(self, user_message: str, ai_response: str) -> List[str]:
        """Detect which platform features are being discussed."""
        features = []
        combined_text = (user_message + " " + ai_response).lower()
        
        feature_keywords = {
            'cv_upload': ['cv', 'resume', 'upload', 'curriculum vitae'],
            'portfolio_generation': ['portfolio', 'website', 'showcase', 'generate'],
            'job_search': ['job', 'position', 'career', 'employment', 'hiring'],
            'company_discovery': ['company', 'employer', 'organization', 'follow'],
            'peer_groups': ['network', 'group', 'peer', 'connect', 'community']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                features.append(feature)
        
        return features


class AnonymousChatService:
    """
    Service for managing anonymous AI chat conversations with limits.
    """
    
    def __init__(self):
        self.ai_service = AIServiceFactory.create_conversational_service()
    
    def send_anonymous_message(
        self, 
        session_key: str, 
        ip_address: str, 
        message: str,
        session_id: Optional[str] = None
    ) -> Tuple[ChatMessage, ChatMessage]:
        """
        Send a message from an anonymous user.
        
        Args:
            session_key: Session key for anonymous user
            ip_address: IP address of the user
            message: The message content
            session_id: Optional existing session ID
            
        Returns:
            Tuple of (user_message, ai_response)
        """
        # Get or create anonymous session
        session = self._get_or_create_anonymous_session(session_key, session_id)
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message,
            status='completed'
        )
        
        # Create AI response message (initially pending)
        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content='',
            status='processing'
        )
        
        try:
            # Generate AI response for anonymous user
            ai_response = self._generate_anonymous_ai_response(message, session)
            
            # Update AI message with response
            ai_message.content = ai_response
            ai_message.status = 'completed'
            ai_message.save()
            
            # Update session timestamp
            session.updated_at = timezone.now()
            session.save()
            
            logger.info(f"Successfully processed anonymous message in session {session.id}")
            
        except Exception as e:
            logger.error(f"Error processing anonymous message in session {session.id}: {e}")
            ai_message.content = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
            ai_message.status = 'failed'
            ai_message.save()
        
        return user_message, ai_message
    
    def _get_or_create_anonymous_session(self, session_key: str, session_id: Optional[str] = None) -> ChatSession:
        """Get or create anonymous chat session."""
        if session_id:
            try:
                session = ChatSession.objects.get(
                    id=session_id, 
                    session_key=session_key, 
                    is_active=True,
                    is_anonymous=True
                )
                return session
            except ChatSession.DoesNotExist:
                logger.warning(f"Anonymous session {session_id} not found, creating new session")
        
        # Create new anonymous session
        session = ChatSession.objects.create(
            session_key=session_key,
            is_anonymous=True,
            title="Anonymous Chat"
        )
        
        logger.info(f"Created new anonymous chat session {session.id}")
        return session
    
    def _generate_anonymous_ai_response(self, message: str, session: ChatSession) -> str:
        """Generate AI response for anonymous users with limited context."""
        try:
            # Get limited conversation history (last 3 messages only)
            recent_messages = session.messages.order_by('-created_at')[:3]
            context_messages = []
            
            for msg in reversed(recent_messages):
                context_messages.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            # Build limited context for anonymous users
            context = {
                'user_profile': {
                    'name': 'Guest',
                    'is_anonymous': True
                },
                'conversation_history': context_messages,
                'session_id': str(session.id),
                'platform_features': {
                    'cv_upload': False,  # Disabled for anonymous users
                    'portfolio_generation': False,  # Disabled for anonymous users
                    'job_search': True,  # Limited access
                    'company_discovery': True,  # Limited access
                    'peer_groups': False  # Disabled for anonymous users
                },
                'anonymous_limitations': {
                    'message_limit': 5,
                    'registration_required': True,
                    'limited_features': True
                }
            }
            
            input_data = {
                'message': message,
                'context': context.get('conversation_history', []),
                'user_profile': context.get('user_profile', {}),
                'anonymous_mode': True
            }
            
            response = self.ai_service.process(input_data)
            
            # Add registration prompt if this is getting close to limit
            message_count = session.message_count
            if message_count >= 3:  # Start prompting at message 3
                response += f"\n\n💡 You have {5 - (message_count // 2)} messages remaining. Register for unlimited chat and access to all features!"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating anonymous AI response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again, or consider registering for a better experience!"


class PlatformIntegrationService:
    """
    Service for integrating chat with platform features.
    """
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def handle_cv_analysis_request(self, user: User, session_id: str) -> Dict[str, Any]:
        """Handle request to analyze user's CV."""
        try:
            profile = user.profile
            if not profile.cv_file:
                return {
                    'success': False,
                    'message': "You haven't uploaded a CV yet. Would you like me to guide you through the upload process?"
                }
            
            # Trigger CV analysis (this would typically be done asynchronously)
            from koroh_platform.utils.cv_analysis_service import analyze_cv_file
            
            analysis_result = analyze_cv_file(profile.cv_file.path)
            
            return {
                'success': True,
                'message': "I've analyzed your CV! Here's what I found:",
                'data': {
                    'skills_count': len(analysis_result.skills),
                    'experience_years': len(analysis_result.work_experience),
                    'education_count': len(analysis_result.education),
                    'key_skills': analysis_result.skills[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing CV for user {user.id}: {e}")
            return {
                'success': False,
                'message': "I encountered an error while analyzing your CV. Please try again later."
            }
    
    def handle_portfolio_generation_request(self, user: User, session_id: str) -> Dict[str, Any]:
        """Handle request to generate portfolio."""
        try:
            profile = user.profile
            if not profile.cv_file:
                return {
                    'success': False,
                    'message': "To generate a portfolio, I'll need your CV first. Would you like to upload one?"
                }
            
            # Check if portfolio already exists
            if profile.portfolio_url:
                return {
                    'success': True,
                    'message': f"You already have a portfolio! You can view it at: {profile.portfolio_url}. Would you like me to generate a new one with a different template?"
                }
            
            return {
                'success': True,
                'message': "I can help you generate a professional portfolio! What style would you prefer: Modern, Classic, or Creative?",
                'action_required': 'portfolio_template_selection'
            }
            
        except Exception as e:
            logger.error(f"Error handling portfolio generation for user {user.id}: {e}")
            return {
                'success': False,
                'message': "I encountered an error while preparing your portfolio generation. Please try again later."
            }
    
    def handle_job_recommendations_request(self, user: User, session_id: str) -> Dict[str, Any]:
        """Handle request for job recommendations."""
        try:
            # This would integrate with the job recommendation service
            from jobs.services import get_personalized_job_recommendations
            
            recommendations = get_personalized_job_recommendations(user, limit=3)
            
            if not recommendations:
                return {
                    'success': True,
                    'message': "I don't have any specific job recommendations for you right now. Let me help you improve your profile to get better matches!"
                }
            
            job_summaries = []
            for job in recommendations:
                job_summaries.append({
                    'title': job.title,
                    'company': job.company.name,
                    'location': job.location,
                    'match_score': getattr(job, 'match_score', 85)
                })
            
            return {
                'success': True,
                'message': f"I found {len(recommendations)} great job opportunities for you!",
                'data': {
                    'recommendations': job_summaries,
                    'total_count': len(recommendations)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting job recommendations for user {user.id}: {e}")
            return {
                'success': False,
                'message': "I'm having trouble accessing job recommendations right now. Please try again later."
            }