from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatContext


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'content_preview', 'status', 'created_at']
    list_filter = ['role', 'status', 'created_at']
    search_fields = ['session__user__email', 'content']
    readonly_fields = ['id', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session__user')


@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = ['session', 'last_ai_action', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['session__user__email', 'last_ai_action']
    readonly_fields = ['updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session__user')