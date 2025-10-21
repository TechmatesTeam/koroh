from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import uuid

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
    """
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='context')
    user_profile_data = models.JSONField(default=dict, blank=True)
    conversation_summary = models.TextField(blank=True)
    active_features = models.JSONField(default=list, blank=True)  # Features being discussed
    last_ai_action = models.CharField(max_length=100, blank=True)
    context_data = models.JSONField(default=dict, blank=True)  # Additional context
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Context for {self.session}"