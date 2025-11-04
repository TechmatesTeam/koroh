from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import uuid
from typing import Dict, Any

User = get_user_model()


class ChatSession(models.Model):
    """
    Represents a chat session between a user and the AI assistant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True, help_text="For anonymous users")
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        if self.user:
            return f"Chat Session {self.id} - {self.user.email}"
        return f"Anonymous Chat Session {self.id} - {self.session_key}"
    
    def save(self, *args, **kwargs):
        # Auto-generate title from first message if not set
        if not self.title and self.messages.exists():
            first_message = self.messages.first()
            if first_message:
                self.title = first_message.content[:50] + "..." if len(first_message.content) > 50 else first_message.content
        super().save(*args, **kwargs)
    
    @property
    def message_count(self):
        """Get the number of messages in this session."""
        return self.messages.count()


class AnonymousChatLimit(models.Model):
    """
    Tracks chat limits for anonymous users based on session key or IP address.
    """
    session_key = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    message_count = models.IntegerField(default=0)
    first_message_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session_key', 'ip_address']
        
    def __str__(self):
        return f"Anonymous limit {self.session_key} - {self.message_count} messages"
    
    @classmethod
    def get_or_create_limit(cls, session_key, ip_address):
        """Get or create anonymous chat limit tracker."""
        limit, created = cls.objects.get_or_create(
            session_key=session_key,
            ip_address=ip_address,
            defaults={'message_count': 0}
        )
        return limit
    
    @classmethod
    def check_limit_exceeded(cls, session_key, ip_address, max_messages=5):
        """Check if anonymous user has exceeded message limit."""
        try:
            limit = cls.objects.get(session_key=session_key, ip_address=ip_address)
            return limit.message_count >= max_messages
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def increment_count(cls, session_key, ip_address):
        """Increment message count for anonymous user."""
        limit = cls.get_or_create_limit(session_key, ip_address)
        limit.message_count += 1
        limit.save()
        return limit


class ChatMessage(models.Model):
    """
    Represents individual messages in a chat session.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ChatContext(models.Model):
    """
    Stores contextual information for chat sessions to maintain conversation state.
    Enhanced with better context tracking and conversation memory.
    """
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='context')
    user_profile_data = models.JSONField(default=dict, blank=True)
    conversation_summary = models.TextField(blank=True)
    active_features = models.JSONField(default=list, blank=True)  # Features being discussed
    last_ai_action = models.CharField(max_length=100, blank=True)
    context_data = models.JSONField(default=dict, blank=True)  # Additional context
    
    # Enhanced context tracking
    conversation_topics = models.JSONField(default=list, blank=True)  # Topics discussed
    user_intent_history = models.JSONField(default=list, blank=True)  # User intents over time
    conversation_stage = models.CharField(max_length=50, default='initial', blank=True)  # greeting, exploration, task_focused, closing
    user_preferences = models.JSONField(default=dict, blank=True)  # Learned user preferences
    mentioned_entities = models.JSONField(default=dict, blank=True)  # Companies, skills, etc. mentioned
    follow_up_actions = models.JSONField(default=list, blank=True)  # Pending actions to follow up on
    
    # Conversation memory
    key_insights = models.JSONField(default=list, blank=True)  # Important insights about user
    conversation_goals = models.JSONField(default=list, blank=True)  # User's stated goals
    previous_recommendations = models.JSONField(default=list, blank=True)  # Past recommendations given
    
    # Context metadata
    context_confidence = models.FloatField(default=0.0)  # Confidence in context understanding
    last_context_update = models.DateTimeField(auto_now=True)
    context_version = models.IntegerField(default=1)  # For context evolution tracking
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Context"
        verbose_name_plural = "Chat Contexts"
    
    def __str__(self):
        return f"Context for {self.session} (Stage: {self.conversation_stage})"
    
    def add_topic(self, topic: str, confidence: float = 1.0):
        """Add a new topic to the conversation topics list."""
        if not self.conversation_topics:
            self.conversation_topics = []
        
        # Add topic with timestamp and confidence
        topic_entry = {
            'topic': topic,
            'confidence': confidence,
            'first_mentioned': timezone.now().isoformat(),
            'mention_count': 1
        }
        
        # Check if topic already exists
        existing_topic = None
        for i, existing in enumerate(self.conversation_topics):
            if existing.get('topic', '').lower() == topic.lower():
                existing_topic = i
                break
        
        if existing_topic is not None:
            # Update existing topic
            self.conversation_topics[existing_topic]['mention_count'] += 1
            self.conversation_topics[existing_topic]['last_mentioned'] = timezone.now().isoformat()
        else:
            # Add new topic
            self.conversation_topics.append(topic_entry)
        
        # Keep only the most recent 20 topics
        if len(self.conversation_topics) > 20:
            self.conversation_topics = self.conversation_topics[-20:]
    
    def add_user_intent(self, intent: str, confidence: float = 1.0):
        """Add a detected user intent to the history."""
        if not self.user_intent_history:
            self.user_intent_history = []
        
        intent_entry = {
            'intent': intent,
            'confidence': confidence,
            'timestamp': timezone.now().isoformat()
        }
        
        self.user_intent_history.append(intent_entry)
        
        # Keep only the most recent 15 intents
        if len(self.user_intent_history) > 15:
            self.user_intent_history = self.user_intent_history[-15:]
    
    def add_entity(self, entity_type: str, entity_value: str, confidence: float = 1.0):
        """Add a mentioned entity (company, skill, etc.) to the context."""
        if not self.mentioned_entities:
            self.mentioned_entities = {}
        
        if entity_type not in self.mentioned_entities:
            self.mentioned_entities[entity_type] = []
        
        entity_entry = {
            'value': entity_value,
            'confidence': confidence,
            'first_mentioned': timezone.now().isoformat(),
            'mention_count': 1
        }
        
        # Check if entity already exists
        existing_entity = None
        for i, existing in enumerate(self.mentioned_entities[entity_type]):
            if existing.get('value', '').lower() == entity_value.lower():
                existing_entity = i
                break
        
        if existing_entity is not None:
            # Update existing entity
            self.mentioned_entities[entity_type][existing_entity]['mention_count'] += 1
            self.mentioned_entities[entity_type][existing_entity]['last_mentioned'] = timezone.now().isoformat()
        else:
            # Add new entity
            self.mentioned_entities[entity_type].append(entity_entry)
        
        # Keep only the most recent 10 entities per type
        if len(self.mentioned_entities[entity_type]) > 10:
            self.mentioned_entities[entity_type] = self.mentioned_entities[entity_type][-10:]
    
    def add_key_insight(self, insight: str, category: str = 'general'):
        """Add a key insight about the user."""
        if not self.key_insights:
            self.key_insights = []
        
        insight_entry = {
            'insight': insight,
            'category': category,
            'timestamp': timezone.now().isoformat(),
            'confidence': 1.0
        }
        
        self.key_insights.append(insight_entry)
        
        # Keep only the most recent 10 insights
        if len(self.key_insights) > 10:
            self.key_insights = self.key_insights[-10:]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context for AI processing."""
        return {
            'conversation_stage': self.conversation_stage,
            'active_topics': [t.get('topic') for t in (self.conversation_topics or [])[-5:]],
            'recent_intents': [i.get('intent') for i in (self.user_intent_history or [])[-3:]],
            'key_entities': {
                entity_type: [e.get('value') for e in entities[-3:]]
                for entity_type, entities in (self.mentioned_entities or {}).items()
            },
            'user_goals': self.conversation_goals or [],
            'key_insights': [i.get('insight') for i in (self.key_insights or [])[-3:]],
            'context_confidence': self.context_confidence,
            'active_features': self.active_features or []
        }