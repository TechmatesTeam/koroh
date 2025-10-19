"""
Serializers for peer groups app.

This module defines the DRF serializers for peer group models,
handling API serialization and validation.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PeerGroup, GroupMembership, GroupAdminship,
    GroupPost, GroupComment
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'profile_picture']
        read_only_fields = ['id', 'email', 'full_name']


class GroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for group membership."""
    
    user = UserBasicSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    invited_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = GroupMembership
        fields = [
            'id', 'user', 'group', 'group_name', 'status', 'role',
            'joined_at', 'invited_by', 'invitation_message',
            'last_activity', 'post_count', 'comment_count',
            'notifications_enabled', 'email_notifications'
        ]
        read_only_fields = [
            'id', 'user', 'group_name', 'joined_at', 'last_activity',
            'post_count', 'comment_count'
        ]


class GroupAdminshipSerializer(serializers.ModelSerializer):
    """Serializer for group adminship."""
    
    user = UserBasicSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    granted_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = GroupAdminship
        fields = [
            'id', 'user', 'group', 'group_name', 'role', 'granted_by',
            'can_manage_members', 'can_moderate_content', 'can_edit_group',
            'granted_at'
        ]
        read_only_fields = ['id', 'user', 'group_name', 'granted_by', 'granted_at']


class PeerGroupListSerializer(serializers.ModelSerializer):
    """Serializer for peer group list view."""
    
    created_by = UserBasicSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerGroup
        fields = [
            'id', 'name', 'slug', 'description', 'tagline', 'group_type',
            'industry', 'privacy_level', 'member_count', 'post_count',
            'activity_score', 'image', 'created_by', 'is_active',
            'is_featured', 'created_at', 'last_activity', 'is_member', 'can_join'
        ]
        read_only_fields = [
            'id', 'slug', 'member_count', 'post_count', 'activity_score',
            'created_at', 'last_activity', 'is_member', 'can_join'
        ]
    
    def get_is_member(self, obj):
        """Check if the current user is a member of this group."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False
    
    def get_can_join(self, obj):
        """Check if the current user can join this group."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_join(request.user)
        return False


class PeerGroupDetailSerializer(serializers.ModelSerializer):
    """Serializer for peer group detail view."""
    
    created_by = UserBasicSerializer(read_only=True)
    admins = UserBasicSerializer(many=True, read_only=True)
    recent_members = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    membership_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerGroup
        fields = [
            'id', 'name', 'slug', 'description', 'tagline', 'group_type',
            'industry', 'skills', 'experience_level', 'location',
            'privacy_level', 'max_members', 'created_by', 'admins',
            'image', 'cover_image', 'rules', 'welcome_message',
            'is_active', 'is_featured', 'member_count', 'post_count',
            'activity_score', 'created_at', 'updated_at', 'last_activity',
            'recent_members', 'is_member', 'is_admin', 'can_join',
            'membership_status'
        ]
        read_only_fields = [
            'id', 'slug', 'created_by', 'admins', 'member_count',
            'post_count', 'activity_score', 'created_at', 'updated_at',
            'last_activity', 'recent_members', 'is_member', 'is_admin',
            'can_join', 'membership_status'
        ]
    
    def get_recent_members(self, obj):
        """Get recent members of the group."""
        recent_memberships = obj.group_memberships.filter(
            status='active'
        ).select_related('user').order_by('-joined_at')[:10]
        return UserBasicSerializer([m.user for m in recent_memberships], many=True).data
    
    def get_is_member(self, obj):
        """Check if the current user is a member of this group."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False
    
    def get_is_admin(self, obj):
        """Check if the current user is an admin of this group."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_admin(request.user)
        return False
    
    def get_can_join(self, obj):
        """Check if the current user can join this group."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_join(request.user)
        return False
    
    def get_membership_status(self, obj):
        """Get the current user's membership status."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = GroupMembership.objects.filter(
                user=request.user, group=obj
            ).first()
            return membership.status if membership else None
        return None


class PeerGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating peer groups."""
    
    class Meta:
        model = PeerGroup
        fields = [
            'name', 'description', 'tagline', 'group_type', 'industry',
            'skills', 'experience_level', 'location', 'privacy_level',
            'max_members', 'image', 'cover_image', 'rules', 'welcome_message'
        ]
    
    def create(self, validated_data):
        """Create a new peer group with the current user as creator."""
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class GroupPostSerializer(serializers.ModelSerializer):
    """Serializer for group posts."""
    
    author = UserBasicSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupPost
        fields = [
            'id', 'group', 'group_name', 'author', 'title', 'content',
            'post_type', 'is_pinned', 'is_locked', 'tags',
            'like_count', 'comment_count', 'view_count',
            'created_at', 'updated_at', 'can_edit', 'can_delete'
        ]
        read_only_fields = [
            'id', 'group_name', 'author', 'like_count', 'comment_count',
            'view_count', 'created_at', 'updated_at', 'can_edit', 'can_delete'
        ]
    
    def get_can_edit(self, obj):
        """Check if the current user can edit this post."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.author == request.user or 
                   obj.group.is_admin(request.user))
        return False
    
    def get_can_delete(self, obj):
        """Check if the current user can delete this post."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.author == request.user or 
                   obj.group.is_admin(request.user))
        return False
    
    def create(self, validated_data):
        """Create a new post with the current user as author."""
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)


class GroupCommentSerializer(serializers.ModelSerializer):
    """Serializer for group comments."""
    
    author = UserBasicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupComment
        fields = [
            'id', 'post', 'author', 'parent', 'content', 'like_count',
            'created_at', 'updated_at', 'replies', 'can_edit', 'can_delete'
        ]
        read_only_fields = [
            'id', 'author', 'like_count', 'created_at', 'updated_at',
            'replies', 'can_edit', 'can_delete'
        ]
    
    def get_replies(self, obj):
        """Get replies to this comment."""
        if obj.replies.exists():
            return GroupCommentSerializer(
                obj.replies.all(), 
                many=True, 
                context=self.context
            ).data
        return []
    
    def get_can_edit(self, obj):
        """Check if the current user can edit this comment."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.author == request.user or 
                   obj.post.group.is_admin(request.user))
        return False
    
    def get_can_delete(self, obj):
        """Check if the current user can delete this comment."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (obj.author == request.user or 
                   obj.post.group.is_admin(request.user))
        return False
    
    def create(self, validated_data):
        """Create a new comment with the current user as author."""
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)


class GroupJoinRequestSerializer(serializers.Serializer):
    """Serializer for group join requests."""
    
    message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional message when requesting to join"
    )


class GroupInviteSerializer(serializers.Serializer):
    """Serializer for group invitations."""
    
    user_email = serializers.EmailField(help_text="Email of user to invite")
    message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional invitation message"
    )
    
    def validate_user_email(self, value):
        """Validate that the user exists."""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class GroupMemberActionSerializer(serializers.Serializer):
    """Serializer for member management actions."""
    
    ACTION_CHOICES = [
        ('approve', 'Approve membership'),
        ('reject', 'Reject membership'),
        ('remove', 'Remove member'),
        ('promote', 'Promote to admin'),
        ('demote', 'Remove admin privileges'),
        ('ban', 'Ban member'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional reason for the action"
    )