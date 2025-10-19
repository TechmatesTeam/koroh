"""
Peer group models for Koroh platform.

This module defines the PeerGroup model and related functionality for
professional networking, group management, and communication features.
"""

import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinLengthValidator

User = get_user_model()


def group_image_upload_path(instance, filename):
    """Generate upload path for group images."""
    return f'peer_groups/{instance.id}/{filename}'


class PeerGroup(models.Model):
    """
    Peer group model for professional networking.
    
    Represents professional peer groups that users can create, join,
    and participate in for networking and collaboration.
    """
    
    PRIVACY_LEVELS = [
        ('public', _('Public - Anyone can join')),
        ('private', _('Private - Invitation only')),
        ('restricted', _('Restricted - Request to join')),
    ]
    
    GROUP_TYPES = [
        ('industry', _('Industry Group')),
        ('skill', _('Skill-based Group')),
        ('location', _('Location-based Group')),
        ('experience', _('Experience Level Group')),
        ('interest', _('Interest Group')),
        ('company', _('Company Alumni Group')),
        ('education', _('Educational Group')),
        ('general', _('General Networking')),
    ]
    
    # Basic group information
    name = models.CharField(
        _('group name'),
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text=_('Name of the peer group')
    )
    slug = models.SlugField(
        _('slug'),
        max_length=200,
        unique=True,
        help_text=_('URL-friendly group identifier')
    )
    description = models.TextField(
        _('group description'),
        help_text=_('Detailed description of the group purpose and goals')
    )
    tagline = models.CharField(
        _('tagline'),
        max_length=200,
        blank=True,
        help_text=_('Short group tagline or mission statement')
    )
    
    # Group categorization
    group_type = models.CharField(
        _('group type'),
        max_length=50,
        choices=GROUP_TYPES,
        default='general',
        help_text=_('Type of peer group')
    )
    industry = models.CharField(
        _('industry'),
        max_length=100,
        blank=True,
        help_text=_('Primary industry focus (if applicable)')
    )
    skills = models.JSONField(
        _('relevant skills'),
        default=list,
        blank=True,
        help_text=_('Skills relevant to this group')
    )
    experience_level = models.CharField(
        _('target experience level'),
        max_length=50,
        blank=True,
        help_text=_('Target experience level for members')
    )
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('Geographic focus (if applicable)')
    )
    
    # Group settings
    privacy_level = models.CharField(
        _('privacy level'),
        max_length=20,
        choices=PRIVACY_LEVELS,
        default='public',
        help_text=_('Group privacy and access control')
    )
    max_members = models.PositiveIntegerField(
        _('maximum members'),
        blank=True,
        null=True,
        help_text=_('Maximum number of members (optional)')
    )
    
    # Group management
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_peer_groups',
        verbose_name=_('creator')
    )
    admins = models.ManyToManyField(
        User,
        through='GroupAdminship',
        through_fields=('group', 'user'),
        related_name='admin_peer_groups',
        blank=True,
        help_text=_('Group administrators')
    )
    members = models.ManyToManyField(
        User,
        through='GroupMembership',
        through_fields=('group', 'user'),
        related_name='peer_groups',
        blank=True,
        help_text=_('Group members')
    )
    
    # Group media
    image = models.ImageField(
        _('group image'),
        upload_to=group_image_upload_path,
        blank=True,
        null=True,
        help_text=_('Group profile image')
    )
    cover_image = models.ImageField(
        _('cover image'),
        upload_to=group_image_upload_path,
        blank=True,
        null=True,
        help_text=_('Group cover/banner image')
    )
    
    # Group rules and guidelines
    rules = models.TextField(
        _('group rules'),
        blank=True,
        help_text=_('Group rules and guidelines for members')
    )
    welcome_message = models.TextField(
        _('welcome message'),
        blank=True,
        help_text=_('Message shown to new members')
    )
    
    # Group status and metrics
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the group is active')
    )
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('Whether the group is featured in recommendations')
    )
    member_count = models.PositiveIntegerField(
        _('member count'),
        default=0,
        help_text=_('Cached member count for performance')
    )
    post_count = models.PositiveIntegerField(
        _('post count'),
        default=0,
        help_text=_('Number of posts in the group')
    )
    activity_score = models.FloatField(
        _('activity score'),
        default=0.0,
        help_text=_('Group activity score for recommendations')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_activity = models.DateTimeField(
        _('last activity'),
        auto_now_add=True,
        help_text=_('Last activity in the group')
    )
    
    class Meta:
        verbose_name = _('Peer Group')
        verbose_name_plural = _('Peer Groups')
        ordering = ['-last_activity', '-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['group_type']),
            models.Index(fields=['industry']),
            models.Index(fields=['privacy_level']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['member_count']),
            models.Index(fields=['activity_score']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to generate slug if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the absolute URL for this group."""
        return reverse('peer_groups:detail', kwargs={'slug': self.slug})
    
    @property
    def is_full(self):
        """Check if the group has reached maximum capacity."""
        if not self.max_members:
            return False
        return self.member_count >= self.max_members
    
    @property
    def can_join_freely(self):
        """Check if users can join without approval."""
        return self.privacy_level == 'public' and not self.is_full
    
    @property
    def requires_approval(self):
        """Check if joining requires approval."""
        return self.privacy_level in ['private', 'restricted']
    
    def get_member_count(self):
        """Get the current member count."""
        return self.members.count()
    
    def update_member_count(self):
        """Update the cached member count."""
        self.member_count = self.get_member_count()
        self.save(update_fields=['member_count'])
    
    def update_activity_score(self):
        """Update the group activity score based on recent activity."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate activity score based on recent posts and member interactions
        recent_date = timezone.now() - timedelta(days=30)
        recent_posts = self.posts.filter(created_at__gte=recent_date).count()
        recent_members = self.groupmembership_set.filter(joined_at__gte=recent_date).count()
        
        # Simple activity score calculation
        activity_score = (recent_posts * 2) + recent_members + (self.member_count * 0.1)
        self.activity_score = min(activity_score, 100.0)  # Cap at 100
        self.save(update_fields=['activity_score'])
    
    def update_last_activity(self):
        """Update the last activity timestamp."""
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def is_member(self, user):
        """Check if a user is a member of this group."""
        return self.members.filter(id=user.id).exists()
    
    def is_admin(self, user):
        """Check if a user is an admin of this group."""
        return user == self.created_by or self.admins.filter(id=user.id).exists()
    
    def can_user_join(self, user):
        """Check if a user can join this group."""
        if self.is_member(user):
            return False
        if self.is_full:
            return False
        return True
    
    def add_skill(self, skill):
        """Add a skill to the group's skill list."""
        if not self.skills:
            self.skills = []
        if skill not in self.skills:
            self.skills.append(skill)
            self.save(update_fields=['skills'])
    
    def remove_skill(self, skill):
        """Remove a skill from the group's skill list."""
        if self.skills and skill in self.skills:
            self.skills.remove(skill)
            self.save(update_fields=['skills'])


class GroupMembership(models.Model):
    """
    Through model for group membership relationship.
    
    Tracks user membership in peer groups with additional metadata
    about the membership status and activity.
    """
    
    MEMBERSHIP_STATUS = [
        ('active', _('Active Member')),
        ('pending', _('Pending Approval')),
        ('invited', _('Invited')),
        ('banned', _('Banned')),
        ('left', _('Left Group')),
    ]
    
    MEMBER_ROLES = [
        ('member', _('Member')),
        ('moderator', _('Moderator')),
        ('admin', _('Administrator')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name=_('user')
    )
    group = models.ForeignKey(
        PeerGroup,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name=_('group')
    )
    
    # Membership details
    status = models.CharField(
        _('membership status'),
        max_length=20,
        choices=MEMBERSHIP_STATUS,
        default='active',
        help_text=_('Current membership status')
    )
    role = models.CharField(
        _('member role'),
        max_length=20,
        choices=MEMBER_ROLES,
        default='member',
        help_text=_('Role within the group')
    )
    
    # Membership metadata
    joined_at = models.DateTimeField(
        _('joined at'),
        auto_now_add=True,
        help_text=_('When the user joined the group')
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='group_invitations_sent',
        verbose_name=_('invited by'),
        help_text=_('User who invited this member (if applicable)')
    )
    invitation_message = models.TextField(
        _('invitation message'),
        blank=True,
        help_text=_('Message sent with the invitation')
    )
    
    # Activity tracking
    last_activity = models.DateTimeField(
        _('last activity'),
        auto_now_add=True,
        help_text=_('Last activity in the group')
    )
    post_count = models.PositiveIntegerField(
        _('post count'),
        default=0,
        help_text=_('Number of posts by this member')
    )
    comment_count = models.PositiveIntegerField(
        _('comment count'),
        default=0,
        help_text=_('Number of comments by this member')
    )
    
    # Notification preferences
    notifications_enabled = models.BooleanField(
        _('notifications enabled'),
        default=True,
        help_text=_('Whether to receive group notifications')
    )
    email_notifications = models.BooleanField(
        _('email notifications'),
        default=True,
        help_text=_('Whether to receive email notifications')
    )
    
    class Meta:
        verbose_name = _('Group Membership')
        verbose_name_plural = _('Group Memberships')
        unique_together = ['user', 'group']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['group', 'status']),
            models.Index(fields=['joined_at']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.group.name}"
    
    def save(self, *args, **kwargs):
        """Override save to update group member count."""
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = GroupMembership.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)
        
        # Update group member count if status changed
        if is_new or old_status != self.status:
            self.group.update_member_count()
    
    def delete(self, *args, **kwargs):
        """Override delete to update group member count."""
        group = self.group
        super().delete(*args, **kwargs)
        group.update_member_count()
    
    def update_activity(self):
        """Update the last activity timestamp."""
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
        self.group.update_last_activity()
    
    def increment_post_count(self):
        """Increment the post count for this member."""
        self.post_count += 1
        self.save(update_fields=['post_count'])
    
    def increment_comment_count(self):
        """Increment the comment count for this member."""
        self.comment_count += 1
        self.save(update_fields=['comment_count'])
    
    @property
    def is_active(self):
        """Check if the membership is active."""
        return self.status == 'active'
    
    @property
    def is_pending(self):
        """Check if the membership is pending approval."""
        return self.status == 'pending'
    
    @property
    def can_post(self):
        """Check if the member can post in the group."""
        return self.status == 'active'
    
    @property
    def can_moderate(self):
        """Check if the member can moderate the group."""
        return self.role in ['moderator', 'admin'] and self.status == 'active'


class GroupAdminship(models.Model):
    """
    Through model for group administration relationship.
    
    Tracks users who have administrative privileges in peer groups.
    """
    
    ADMIN_ROLES = [
        ('admin', _('Administrator')),
        ('moderator', _('Moderator')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_adminships',
        verbose_name=_('user')
    )
    group = models.ForeignKey(
        PeerGroup,
        on_delete=models.CASCADE,
        related_name='group_adminships',
        verbose_name=_('group')
    )
    
    # Admin details
    role = models.CharField(
        _('admin role'),
        max_length=20,
        choices=ADMIN_ROLES,
        default='admin',
        help_text=_('Administrative role')
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='granted_adminships',
        verbose_name=_('granted by'),
        help_text=_('User who granted admin privileges')
    )
    
    # Permissions
    can_manage_members = models.BooleanField(
        _('can manage members'),
        default=True,
        help_text=_('Can approve/remove members')
    )
    can_moderate_content = models.BooleanField(
        _('can moderate content'),
        default=True,
        help_text=_('Can moderate posts and comments')
    )
    can_edit_group = models.BooleanField(
        _('can edit group'),
        default=False,
        help_text=_('Can edit group settings')
    )
    
    # Timestamps
    granted_at = models.DateTimeField(_('granted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Group Adminship')
        verbose_name_plural = _('Group Adminships')
        unique_together = ['user', 'group']
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['user', 'role']),
            models.Index(fields=['group', 'role']),
            models.Index(fields=['granted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} of {self.group.name}"


class GroupPost(models.Model):
    """
    Model for posts within peer groups.
    
    Represents posts, discussions, and content shared within peer groups.
    """
    
    POST_TYPES = [
        ('discussion', _('Discussion')),
        ('question', _('Question')),
        ('announcement', _('Announcement')),
        ('resource', _('Resource Share')),
        ('event', _('Event')),
        ('job', _('Job Posting')),
    ]
    
    group = models.ForeignKey(
        PeerGroup,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('group')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_posts',
        verbose_name=_('author')
    )
    
    # Post content
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('Post title')
    )
    content = models.TextField(
        _('content'),
        help_text=_('Post content')
    )
    post_type = models.CharField(
        _('post type'),
        max_length=20,
        choices=POST_TYPES,
        default='discussion',
        help_text=_('Type of post')
    )
    
    # Post metadata
    is_pinned = models.BooleanField(
        _('pinned'),
        default=False,
        help_text=_('Whether the post is pinned to the top')
    )
    is_locked = models.BooleanField(
        _('locked'),
        default=False,
        help_text=_('Whether comments are disabled')
    )
    tags = models.JSONField(
        _('tags'),
        default=list,
        blank=True,
        help_text=_('Post tags for categorization')
    )
    
    # Engagement metrics
    like_count = models.PositiveIntegerField(
        _('like count'),
        default=0,
        help_text=_('Number of likes')
    )
    comment_count = models.PositiveIntegerField(
        _('comment count'),
        default=0,
        help_text=_('Number of comments')
    )
    view_count = models.PositiveIntegerField(
        _('view count'),
        default=0,
        help_text=_('Number of views')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Group Post')
        verbose_name_plural = _('Group Posts')
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['post_type']),
            models.Index(fields=['is_pinned', 'created_at']),
            models.Index(fields=['like_count']),
            models.Index(fields=['comment_count']),
        ]
    
    def __str__(self):
        return f"{self.title} in {self.group.name}"
    
    def save(self, *args, **kwargs):
        """Override save to update group post count and activity."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.group.post_count += 1
            self.group.save(update_fields=['post_count'])
            self.group.update_last_activity()
            
            # Update member post count
            membership = GroupMembership.objects.filter(
                user=self.author, 
                group=self.group
            ).first()
            if membership:
                membership.increment_post_count()
    
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_like_count(self):
        """Increment the like count."""
        self.like_count += 1
        self.save(update_fields=['like_count'])
    
    def decrement_like_count(self):
        """Decrement the like count."""
        if self.like_count > 0:
            self.like_count -= 1
            self.save(update_fields=['like_count'])
    
    def add_tag(self, tag):
        """Add a tag to the post."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])


class GroupComment(models.Model):
    """
    Model for comments on group posts.
    
    Represents comments and replies within group discussions.
    """
    
    post = models.ForeignKey(
        GroupPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('post')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_comments',
        verbose_name=_('author')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies',
        verbose_name=_('parent comment'),
        help_text=_('Parent comment for nested replies')
    )
    
    # Comment content
    content = models.TextField(
        _('content'),
        help_text=_('Comment content')
    )
    
    # Engagement metrics
    like_count = models.PositiveIntegerField(
        _('like count'),
        default=0,
        help_text=_('Number of likes')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Group Comment')
        verbose_name_plural = _('Group Comments')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        """Override save to update post comment count."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.post.comment_count += 1
            self.post.save(update_fields=['comment_count'])
            
            # Update member comment count
            membership = GroupMembership.objects.filter(
                user=self.author, 
                group=self.post.group
            ).first()
            if membership:
                membership.increment_comment_count()
    
    def increment_like_count(self):
        """Increment the like count."""
        self.like_count += 1
        self.save(update_fields=['like_count'])
    
    def decrement_like_count(self):
        """Decrement the like count."""
        if self.like_count > 0:
            self.like_count -= 1
            self.save(update_fields=['like_count'])
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment."""
        return self.parent is not None