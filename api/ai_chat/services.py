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
from django.conf import settings
from koroh_platform.utils.ai_services import AIServiceFactory, ConversationalAIService
from .models import ChatSession, ChatMessage, ChatContext, AnonymousChatLimit

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing AI chat conversations and context.
    """
    
    def __init__(self):
        self.ai_service = AIServiceFactory.create_concise_chat_service()
    
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
        """Build enhanced conversation context for AI service with context awareness."""
        # Get recent messages for context (increased for better context)
        recent_messages = session.messages.order_by('-created_at')[:15]
        context_messages = []
        
        for msg in reversed(recent_messages):
            context_messages.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            })
        
        # Get enhanced session context
        session_context = getattr(session, 'context', None)
        user_profile = session_context.user_profile_data if session_context else {}
        
        # Build enhanced context with conversation awareness
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
        
        # Add enhanced context information if available
        if session_context:
            context_summary = session_context.get_context_summary()
            context.update({
                'conversation_context': {
                    'stage': context_summary.get('conversation_stage', 'initial'),
                    'active_topics': context_summary.get('active_topics', []),
                    'recent_intents': context_summary.get('recent_intents', []),
                    'key_entities': context_summary.get('key_entities', {}),
                    'user_goals': context_summary.get('user_goals', []),
                    'key_insights': context_summary.get('key_insights', []),
                    'context_confidence': context_summary.get('context_confidence', 0.0),
                    'active_features': context_summary.get('active_features', [])
                },
                'conversation_memory': {
                    'summary': session_context.conversation_summary,
                    'previous_recommendations': session_context.previous_recommendations or [],
                    'user_preferences': session_context.user_preferences or {},
                    'follow_up_actions': session_context.follow_up_actions or []
                }
            })
        
        # Add additional context if provided
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _generate_ai_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate context-aware AI response using the enhanced conversational service."""
        try:
            input_data = {
                'message': message,
                'context': context.get('conversation_history', []),
                'user_profile': context.get('user_profile', {}),
                'conversation_context': context.get('conversation_context', {}),
                'conversation_memory': context.get('conversation_memory', {}),
                'concise_mode': True  # Enable concise response mode
            }
            
            response = self.ai_service.process(input_data)
            
            # Post-process to ensure conciseness while maintaining context awareness
            response = self._ensure_response_conciseness(response)
            
            # Optimize based on query type and conversation context
            response = self._optimize_response_for_query_type(message, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm having trouble processing your request. Please try again."
    
    def _ensure_response_conciseness(self, response: str) -> str:
        """Ensure the response meets conciseness standards based on configuration."""
        if not response:
            return response
        
        # Check if concise mode is enabled
        if not getattr(settings, 'AI_CHAT_CONCISE_MODE', True):
            return response
        
        max_chars = getattr(settings, 'AI_CHAT_MAX_RESPONSE_CHARS', 500)
        max_words = getattr(settings, 'AI_CHAT_MAX_RESPONSE_WORDS', 50)
        
        # Apply word limit first
        words = response.split()
        if len(words) > max_words:
            response = ' '.join(words[:max_words])
            if not response.endswith('.'):
                response += '.'
        
        # Apply character limit if still too long
        if len(response) > max_chars:
            # Split into sentences and keep as many as fit
            sentences = response.split('. ')
            truncated = []
            char_count = 0
            
            for sentence in sentences:
                if char_count + len(sentence) + 2 <= max_chars - 10:  # Leave room for punctuation
                    truncated.append(sentence)
                    char_count += len(sentence) + 2
                else:
                    break
            
            if truncated:
                result = '. '.join(truncated)
                if not result.endswith('.'):
                    result += '.'
                return result
            else:
                # If no complete sentences fit, truncate at character limit
                return response[:max_chars-3] + '...'
        
        return response
    
    def _optimize_response_for_query_type(self, message: str, response: str, context: Dict[str, Any] = None) -> str:
        """Optimize response length based on query type, conversation context, and configuration."""
        if not getattr(settings, 'AI_CHAT_ENABLE_CONTEXT_OPTIMIZATION', True):
            return response
        
        message_lower = message.lower()
        conversation_context = context.get('conversation_context', {}) if context else {}
        conversation_stage = conversation_context.get('stage', 'initial')
        
        # Adjust response length based on conversation stage
        stage_multipliers = {
            'greeting': 0.8,  # Shorter for greetings
            'initial': 1.0,   # Standard length
            'exploration': 1.2,  # Slightly longer for exploration
            'task_focused': 1.1,  # Focused but informative
            'follow_up': 0.9   # Shorter for follow-ups
        }
        
        length_multiplier = stage_multipliers.get(conversation_stage, 1.0)
        
        # Very short responses for simple queries
        simple_queries = ['hi', 'hello', 'thanks', 'thank you', 'ok', 'okay', 'yes', 'no']
        if any(query in message_lower for query in simple_queries):
            # Keep response under 15 words for greetings/acknowledgments
            max_words = int(15 * length_multiplier)
            words = response.split()
            if len(words) > max_words:
                return ' '.join(words[:max_words]) + '.'
        
        # Medium responses for specific questions
        question_words = ['what', 'how', 'when', 'where', 'why', 'which', 'who']
        if any(word in message_lower for word in question_words):
            # Keep under 30 words for questions
            max_words = int(30 * length_multiplier)
            words = response.split()
            if len(words) > max_words:
                return ' '.join(words[:max_words]) + '.'
        
        # Context-aware responses for follow-up questions
        follow_up_indicators = ['also', 'additionally', 'furthermore', 'what about', 'and']
        if any(indicator in message_lower for indicator in follow_up_indicators):
            # Shorter responses for follow-ups since context is established
            max_words = int(25 * length_multiplier)
            words = response.split()
            if len(words) > max_words:
                return ' '.join(words[:max_words]) + '.'
        
        # Slightly longer responses for complex requests (but still concise)
        complex_indicators = ['explain', 'describe', 'tell me about', 'help me understand']
        if any(indicator in message_lower for indicator in complex_indicators):
            # Allow up to 45 words for complex explanations
            max_words = int(45 * length_multiplier)
            words = response.split()
            if len(words) > max_words:
                return ' '.join(words[:max_words]) + '.'
        
        return response
    
    def _update_session_context(
        self, 
        session: ChatSession, 
        user_message: str, 
        ai_response: str,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Update session context with enhanced conversation analysis."""
        try:
            context, created = ChatContext.objects.get_or_create(session=session)
            
            # Analyze and update conversation context
            self._analyze_conversation_turn(context, user_message, ai_response)
            
            # Update conversation summary if needed (every 8 messages for better tracking)
            message_count = session.messages.count()
            if message_count % 8 == 0:
                context.conversation_summary = self._generate_conversation_summary(session)
            
            # Detect active features being discussed
            active_features = self._detect_active_features(user_message, ai_response)
            if active_features:
                context.active_features = list(set((context.active_features or []) + active_features))
            
            # Update conversation stage based on interaction patterns
            context.conversation_stage = self._determine_conversation_stage(context, user_message, ai_response)
            
            # Update context confidence based on conversation quality
            context.context_confidence = self._calculate_context_confidence(context, session)
            
            # Update context data
            if additional_context:
                if not context.context_data:
                    context.context_data = {}
                context.context_data.update(additional_context)
            
            # Increment context version for tracking
            context.context_version += 1
            
            context.save()
            
        except Exception as e:
            logger.error(f"Error updating session context: {e}")
    
    def _generate_conversation_summary(self, session: ChatSession) -> str:
        """Generate a concise summary of the conversation for context."""
        try:
            # Limit to fewer messages for more focused summary
            recent_messages = session.messages.order_by('-created_at')[:10]
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content[:100]}..." if len(msg.content) > 100 else f"{msg.role}: {msg.content}"
                for msg in reversed(recent_messages)
            ])
            
            # Use AI to generate concise summary
            summary_input = {
                'message': f"Summarize this conversation in 1-2 sentences:\n\n{conversation_text}",
                'context': [],
                'user_profile': {}
            }
            
            summary = self.ai_service.process(summary_input)
            return summary[:200]  # Reduced from 500 to 200 characters
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Career discussion."
    
    def _analyze_conversation_turn(self, context: 'ChatContext', user_message: str, ai_response: str):
        """Analyze a single conversation turn and update context accordingly."""
        # Detect topics
        topics = self._extract_topics(user_message)
        for topic in topics:
            context.add_topic(topic)
        
        # Detect user intents
        intents = self._detect_user_intents(user_message)
        for intent in intents:
            context.add_user_intent(intent)
        
        # Extract entities (companies, skills, etc.)
        entities = self._extract_entities(user_message)
        for entity_type, entity_values in entities.items():
            for entity_value in entity_values:
                context.add_entity(entity_type, entity_value)
        
        # Detect key insights about the user
        insights = self._extract_user_insights(user_message, ai_response)
        for insight in insights:
            context.add_key_insight(insight['text'], insight['category'])
        
        # Update user goals if mentioned
        goals = self._extract_user_goals(user_message)
        if goals:
            if not context.conversation_goals:
                context.conversation_goals = []
            for goal in goals:
                if goal not in context.conversation_goals:
                    context.conversation_goals.append(goal)
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract conversation topics from user message."""
        topics = []
        message_lower = message.lower()
        
        # Define topic patterns
        topic_patterns = {
            'career_change': ['career change', 'switch career', 'new career', 'career transition'],
            'job_search': ['job search', 'looking for job', 'find job', 'job hunting'],
            'skill_development': ['learn', 'skill', 'training', 'course', 'certification'],
            'networking': ['network', 'connect', 'meet people', 'professional contacts'],
            'salary_negotiation': ['salary', 'negotiate', 'compensation', 'pay raise'],
            'interview_prep': ['interview', 'interview preparation', 'job interview'],
            'resume_help': ['resume', 'cv', 'curriculum vitae'],
            'portfolio_creation': ['portfolio', 'showcase', 'personal website'],
            'company_research': ['company', 'employer', 'organization research'],
            'industry_insights': ['industry', 'market trends', 'sector analysis']
        }
        
        for topic, patterns in topic_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                topics.append(topic)
        
        return topics
    
    def _detect_user_intents(self, message: str) -> List[str]:
        """Detect user intents from the message."""
        intents = []
        message_lower = message.lower()
        
        # Define intent patterns
        intent_patterns = {
            'seeking_advice': ['help', 'advice', 'suggest', 'recommend', 'what should'],
            'requesting_information': ['what is', 'how to', 'tell me about', 'explain'],
            'expressing_frustration': ['frustrated', 'stuck', 'difficult', 'hard', 'struggling'],
            'showing_interest': ['interested', 'sounds good', 'tell me more', 'that looks'],
            'making_decision': ['should I', 'which one', 'better option', 'decide'],
            'requesting_action': ['can you', 'please', 'help me', 'do this'],
            'providing_feedback': ['good', 'bad', 'like', 'dislike', 'prefer'],
            'asking_clarification': ['what do you mean', 'clarify', 'explain more', 'confused']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                intents.append(intent)
        
        return intents
    
    def _extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extract named entities from the message."""
        entities = {
            'companies': [],
            'skills': [],
            'locations': [],
            'job_titles': [],
            'industries': []
        }
        
        message_lower = message.lower()
        
        # Common company names (simplified - in production, use NER)
        company_patterns = ['google', 'microsoft', 'apple', 'amazon', 'facebook', 'meta', 'netflix', 'tesla', 'uber', 'airbnb']
        for company in company_patterns:
            if company in message_lower:
                entities['companies'].append(company.title())
        
        # Common skills
        skill_patterns = ['python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws', 'docker', 'kubernetes', 'machine learning', 'data science']
        for skill in skill_patterns:
            if skill in message_lower:
                entities['skills'].append(skill)
        
        # Common job titles
        job_title_patterns = ['developer', 'engineer', 'manager', 'analyst', 'designer', 'consultant', 'director', 'specialist']
        for title in job_title_patterns:
            if title in message_lower:
                entities['job_titles'].append(title)
        
        # Remove empty lists
        return {k: v for k, v in entities.items() if v}
    
    def _extract_user_insights(self, user_message: str, ai_response: str) -> List[Dict[str, str]]:
        """Extract key insights about the user from the conversation."""
        insights = []
        message_lower = user_message.lower()
        
        # Experience level insights
        if any(phrase in message_lower for phrase in ['new to', 'beginner', 'just started', 'no experience']):
            insights.append({'text': 'User is a beginner in their field', 'category': 'experience_level'})
        elif any(phrase in message_lower for phrase in ['experienced', 'senior', 'years of experience', 'expert']):
            insights.append({'text': 'User has significant experience', 'category': 'experience_level'})
        
        # Career stage insights
        if any(phrase in message_lower for phrase in ['recent graduate', 'just graduated', 'fresh out of']):
            insights.append({'text': 'User is a recent graduate', 'category': 'career_stage'})
        elif any(phrase in message_lower for phrase in ['career change', 'switching careers', 'new field']):
            insights.append({'text': 'User is considering a career change', 'category': 'career_stage'})
        
        # Motivation insights
        if any(phrase in message_lower for phrase in ['passionate about', 'love', 'enjoy', 'excited']):
            insights.append({'text': 'User shows passion for their field', 'category': 'motivation'})
        elif any(phrase in message_lower for phrase in ['burned out', 'tired', 'stressed', 'overwhelmed']):
            insights.append({'text': 'User may be experiencing burnout', 'category': 'motivation'})
        
        return insights
    
    def _extract_user_goals(self, message: str) -> List[str]:
        """Extract user goals from the message."""
        goals = []
        message_lower = message.lower()
        
        goal_patterns = {
            'find_new_job': ['find a job', 'get a job', 'job search', 'looking for work'],
            'career_advancement': ['promotion', 'advance career', 'move up', 'next level'],
            'skill_improvement': ['improve skills', 'learn new skills', 'get better at'],
            'salary_increase': ['higher salary', 'more money', 'better pay', 'increase income'],
            'work_life_balance': ['work life balance', 'flexible work', 'remote work'],
            'industry_change': ['change industry', 'different field', 'new sector']
        }
        
        for goal, patterns in goal_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                goals.append(goal.replace('_', ' ').title())
        
        return goals
    
    def _determine_conversation_stage(self, context: 'ChatContext', user_message: str, ai_response: str) -> str:
        """Determine the current stage of the conversation."""
        message_count = context.session.messages.count()
        message_lower = user_message.lower()
        
        # Initial stage (first few messages)
        if message_count <= 3:
            if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
                return 'greeting'
            else:
                return 'initial'
        
        # Exploration stage (getting to know user needs)
        elif message_count <= 8:
            if any(word in message_lower for word in ['help', 'need', 'looking for', 'want to']):
                return 'exploration'
        
        # Task-focused stage (working on specific tasks)
        elif any(action in message_lower for action in ['analyze', 'generate', 'create', 'find', 'search']):
            return 'task_focused'
        
        # Follow-up stage (continuing previous conversations)
        elif context.conversation_summary and len(context.conversation_summary) > 100:
            return 'follow_up'
        
        # Default to exploration if unclear
        return 'exploration'
    
    def _calculate_context_confidence(self, context: 'ChatContext', session: ChatSession) -> float:
        """Calculate confidence in the current context understanding."""
        confidence_factors = []
        
        # Message count factor (more messages = better context)
        message_count = session.messages.count()
        message_factor = min(message_count / 10.0, 1.0)  # Max confidence at 10+ messages
        confidence_factors.append(message_factor)
        
        # Topic consistency factor
        if context.conversation_topics:
            unique_topics = len(set(t.get('topic') for t in context.conversation_topics))
            topic_factor = min(unique_topics / 5.0, 1.0)  # Max confidence at 5+ topics
            confidence_factors.append(topic_factor)
        
        # User profile completeness factor
        profile_data = context.user_profile_data or {}
        profile_fields = ['name', 'industry', 'experience_level', 'skills']
        profile_completeness = sum(1 for field in profile_fields if profile_data.get(field))
        profile_factor = profile_completeness / len(profile_fields)
        confidence_factors.append(profile_factor)
        
        # Intent clarity factor
        if context.user_intent_history:
            recent_intents = context.user_intent_history[-5:]  # Last 5 intents
            intent_factor = min(len(recent_intents) / 5.0, 1.0)
            confidence_factors.append(intent_factor)
        
        # Calculate weighted average
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.0
    
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
        self.ai_service = AIServiceFactory.create_concise_chat_service()
    
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
        """Generate concise AI response for anonymous users with limited context."""
        try:
            # Get limited conversation history (last 2 messages only for conciseness)
            recent_messages = session.messages.order_by('-created_at')[:2]
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
            
            # Add concise registration prompt if this is getting close to limit
            message_count = session.message_count
            if message_count >= 3:  # Start prompting at message 3
                remaining = 5 - (message_count // 2)
                response += f"\n\n💡 {remaining} messages left. Register for unlimited access!"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating anonymous AI response: {e}")
            return "I'm having trouble right now. Please try again or register for better support!"


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