"""
Admin configuration for peer groups app.

This module defines the Django admin interface for peer group models,
providing comprehensive management capabilities for administrators.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    PeerGroup, GroupMembership, GroupAdminship, 
    GroupPost, GroupComment
)


@admin.register(PeerGroup)
class PeerGroupAdmin(admin.ModelAdmin):
    """Admin interface for PeerGroup model."""
    
    list_display = [
        'name', 'group_type', 'privacy_level', 'member_count', 
        'is_active', 'is_featured', 'created_by', 'created_at'
    ]
    list_filter = [
        'group_type', 'privacy_level', 'is_active', 'is_featured',
        'industry', 'created_at'
    ]
    search_fields = ['name', 'description', 'industry', 'skills']
    readonly_fields = [
        'slug', 'member_count', 'post_count', 'activity_score',
        'created_at', 'updated_at', 'last_activity'
    ]
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'tagline')
        }),
        ('Categorization', {
            'fields': ('group_type', 'industry', 'skills', 'experience_level', 'location')
        }),
        ('Settings', {
            'fields': ('privacy_level', 'max_members', 'created_by')
        }),
        ('Media', {
            'fields': ('image', 'cover_image'),
            'classes': ('collapse',)
        }),
        ('Rules & Guidelines', {
            'fields': ('rules', 'welcome_message'),
            'classes': ('collapse',)
        }),
        ('Status & Metrics', {
            'fields': (
                'is_active', 'is_featured', 'member_count', 
                'post_count', 'activity_score'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('created_by')


class GroupMembershipInline(admin.TabularInline):
    """Inline admin for group memberships."""
    
    model = GroupMembership
    extra = 0
    readonly_fields = ['joined_at', 'last_activity', 'post_count', 'comment_count']
    fields = [
        'user', 'status', 'role', 'joined_at', 'notifications_enabled',
        'post_count', 'comment_count'
    ]


class GroupAdminshipInline(admin.TabularInline):
    """Inline admin for group adminships."""
    
    model = GroupAdminship
    extra = 0
    readonly_fields = ['granted_at']
    fields = [
        'user', 'role', 'granted_by', 'can_manage_members',
        'can_moderate_content', 'can_edit_group', 'granted_at'
    ]


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    """Admin interface for GroupMembership model."""
    
    list_display = [
        'user', 'group', 'status', 'role', 'joined_at',
        'post_count', 'comment_count', 'notifications_enabled'
    ]
    list_filter = [
        'status', 'role', 'notifications_enabled', 'email_notifications',
        'joined_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'group__name'
    ]
    readonly_fields = [
        'joined_at', 'last_activity', 'post_count', 'comment_count'
    ]
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('user', 'group', 'status', 'role')
        }),
        ('Invitation Info', {
            'fields': ('invited_by', 'invitation_message'),
            'classes': ('collapse',)
        }),
        ('Activity Tracking', {
            'fields': ('last_activity', 'post_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Notification Preferences', {
            'fields': ('notifications_enabled', 'email_notifications'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'group', 'invited_by')


@admin.register(GroupAdminship)
class GroupAdminshipAdmin(admin.ModelAdmin):
    """Admin interface for GroupAdminship model."""
    
    list_display = [
        'user', 'group', 'role', 'granted_by', 'granted_at',
        'can_manage_members', 'can_moderate_content', 'can_edit_group'
    ]
    list_filter = [
        'role', 'can_manage_members', 'can_moderate_content',
        'can_edit_group', 'granted_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'group__name'
    ]
    readonly_fields = ['granted_at']
    
    fieldsets = (
        ('Admin Details', {
            'fields': ('user', 'group', 'role', 'granted_by')
        }),
        ('Permissions', {
            'fields': (
                'can_manage_members', 'can_moderate_content', 'can_edit_group'
            )
        }),
        ('Timestamps', {
            'fields': ('granted_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'group', 'granted_by')


class GroupCommentInline(admin.TabularInline):
    """Inline admin for group comments."""
    
    model = GroupComment
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'like_count']
    fields = ['author', 'content', 'parent', 'like_count', 'created_at']


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    """Admin interface for GroupPost model."""
    
    list_display = [
        'title', 'group', 'author', 'post_type', 'is_pinned',
        'like_count', 'comment_count', 'view_count', 'created_at'
    ]
    list_filter = [
        'post_type', 'is_pinned', 'is_locked', 'created_at',
        'group__group_type'
    ]
    search_fields = [
        'title', 'content', 'author__email', 'author__first_name',
        'author__last_name', 'group__name', 'tags'
    ]
    readonly_fields = [
        'like_count', 'comment_count', 'view_count',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Post Details', {
            'fields': ('group', 'author', 'title', 'content', 'post_type')
        }),
        ('Post Settings', {
            'fields': ('is_pinned', 'is_locked', 'tags')
        }),
        ('Engagement Metrics', {
            'fields': ('like_count', 'comment_count', 'view_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [GroupCommentInline]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('group', 'author')


@admin.register(GroupComment)
class GroupCommentAdmin(admin.ModelAdmin):
    """Admin interface for GroupComment model."""
    
    list_display = [
        'post', 'author', 'content_preview', 'parent',
        'like_count', 'created_at'
    ]
    list_filter = ['created_at', 'post__group__group_type']
    search_fields = [
        'content', 'author__email', 'author__first_name',
        'author__last_name', 'post__title'
    ]
    readonly_fields = ['like_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('post', 'author', 'parent', 'content')
        }),
        ('Engagement', {
            'fields': ('like_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show a preview of the comment content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('post', 'author', 'parent')


# Customize admin site header and title
admin.site.site_header = "Koroh Platform Administration"
admin.site.site_title = "Koroh Admin"
admin.site.index_title = "Welcome to Koroh Platform Administration"