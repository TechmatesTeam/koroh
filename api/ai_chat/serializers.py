from rest_framework import serializers
from .models import ChatSession, ChatMessage, ChatContext


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'metadata', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing chat sessions."""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'message_count', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                'role': last_message.role,
                'created_at': last_message.created_at
            }
        return None


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending messages to the AI chat."""
    message = serializers.CharField(max_length=2000)
    session_id = serializers.UUIDField(required=False)
    context = serializers.JSONField(required=False, default=dict)
    
    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()


class ChatContextSerializer(serializers.ModelSerializer):
    """Serializer for chat context."""
    
    class Meta:
        model = ChatContext
        fields = ['user_profile_data', 'conversation_summary', 'active_features', 'last_ai_action', 'context_data', 'updated_at']
        read_only_fields = ['updated_at']