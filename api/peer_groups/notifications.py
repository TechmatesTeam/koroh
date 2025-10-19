"""
Notification services for peer groups app.

This module provides notification functionality for peer group activities
including new posts, comments, member joins, and group updates.
"""

import logging
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import PeerGroup, GroupMembership, GroupPost, GroupComment

User = get_user_model()
logger = logging.getLogger(__name__)


class GroupNotificationService:
    """
    Service for handling peer group notifications.
    
    Manages in-app notifications and email notifications for various
    group activities and events.
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@koroh.com')
    
    def notify_new_member_joined(self, membership: GroupMembership) -> None:
        """
        Notify group admins when a new member joins.
        
        Args:
            membership: The new group membership
        """
        try:
            group = membership.group
            new_member = membership.user
            
            # Get group admins
            admin_users = self._get_group_admins(group)
            
            if not admin_users:
                return
            
            # Prepare notification data
            notification_data = {
                'type': 'new_member_joined',
                'group': group,
                'new_member': new_member,
                'membership': membership
            }
            
            # Send notifications to admins
            for admin in admin_users:
                if admin != new_member:  # Don't notify the new member about themselves
                    self._send_notification(admin, notification_data)
            
            logger.info(f"Sent new member notifications for {new_member.email} joining {group.name}")
            
        except Exception as e:
            logger.error(f"Error sending new member notifications: {e}")
    
    def notify_new_post(self, post: GroupPost) -> None:
        """
        Notify group members about a new post.
        
        Args:
            post: The new group post
        """
        try:
            group = post.group
            author = post.author
            
            # Get group members who want notifications
            members = self._get_notification_enabled_members(group)
            
            if not members:
                return
            
            # Prepare notification data
            notification_data = {
                'type': 'new_post',
                'group': group,
                'post': post,
                'author': author
            }
            
            # Send notifications to members (except author)
            for member in members:
                if member != author:
                    self._send_notification(member, notification_data)
            
            logger.info(f"Sent new post notifications for post '{post.title}' in {group.name}")
            
        except Exception as e:
            logger.error(f"Error sending new post notifications: {e}")
    
    def notify_new_comment(self, comment: GroupComment) -> None:
        """
        Notify relevant users about a new comment.
        
        Args:
            comment: The new comment
        """
        try:
            post = comment.post
            group = post.group
            comment_author = comment.author
            post_author = post.author
            
            # Notify post author if they're not the comment author
            if post_author != comment_author:
                notification_data = {
                    'type': 'comment_on_post',
                    'group': group,
                    'post': post,
                    'comment': comment,
                    'comment_author': comment_author
                }
                self._send_notification(post_author, notification_data)
            
            # If this is a reply to another comment, notify the parent comment author
            if comment.parent and comment.parent.author != comment_author:
                notification_data = {
                    'type': 'reply_to_comment',
                    'group': group,
                    'post': post,
                    'comment': comment,
                    'parent_comment': comment.parent,
                    'comment_author': comment_author
                }
                self._send_notification(comment.parent.author, notification_data)
            
            logger.info(f"Sent comment notifications for comment on '{post.title}'")
            
        except Exception as e:
            logger.error(f"Error sending comment notifications: {e}")
    
    def notify_membership_request(self, membership: GroupMembership) -> None:
        """
        Notify group admins about a new membership request.
        
        Args:
            membership: The pending membership request
        """
        try:
            group = membership.group
            requesting_user = membership.user
            
            # Get group admins
            admin_users = self._get_group_admins(group)
            
            if not admin_users:
                return
            
            # Prepare notification data
            notification_data = {
                'type': 'membership_request',
                'group': group,
                'requesting_user': requesting_user,
                'membership': membership
            }
            
            # Send notifications to admins
            for admin in admin_users:
                self._send_notification(admin, notification_data)
            
            logger.info(f"Sent membership request notifications for {requesting_user.email} to {group.name}")
            
        except Exception as e:
            logger.error(f"Error sending membership request notifications: {e}")
    
    def notify_membership_approved(self, membership: GroupMembership) -> None:
        """
        Notify user that their membership request was approved.
        
        Args:
            membership: The approved membership
        """
        try:
            group = membership.group
            user = membership.user
            
            notification_data = {
                'type': 'membership_approved',
                'group': group,
                'membership': membership
            }
            
            self._send_notification(user, notification_data)
            
            logger.info(f"Sent membership approval notification to {user.email} for {group.name}")
            
        except Exception as e:
            logger.error(f"Error sending membership approval notification: {e}")
    
    def notify_group_invitation(self, membership: GroupMembership) -> None:
        """
        Notify user about a group invitation.
        
        Args:
            membership: The invitation membership
        """
        try:
            group = membership.group
            invited_user = membership.user
            inviter = membership.invited_by
            
            notification_data = {
                'type': 'group_invitation',
                'group': group,
                'invited_user': invited_user,
                'inviter': inviter,
                'membership': membership
            }
            
            self._send_notification(invited_user, notification_data)
            
            logger.info(f"Sent group invitation notification to {invited_user.email} for {group.name}")
            
        except Exception as e:
            logger.error(f"Error sending group invitation notification: {e}")
    
    def _get_group_admins(self, group: PeerGroup) -> List[User]:
        """Get all admin users for a group."""
        admin_users = [group.created_by]  # Creator is always an admin
        
        # Add other admins
        other_admins = group.admins.all()
        admin_users.extend(other_admins)
        
        # Remove duplicates
        return list(set(admin_users))
    
    def _get_notification_enabled_members(self, group: PeerGroup) -> List[User]:
        """Get group members who have notifications enabled."""
        memberships = GroupMembership.objects.filter(
            group=group,
            status='active',
            notifications_enabled=True
        ).select_related('user')
        
        return [membership.user for membership in memberships]
    
    def _send_notification(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send notification to a user (in-app and email if enabled).
        
        Args:
            user: User to send notification to
            notification_data: Notification data dictionary
        """
        try:
            # Create in-app notification (would need a Notification model)
            self._create_in_app_notification(user, notification_data)
            
            # Send email notification if user has email notifications enabled
            membership = GroupMembership.objects.filter(
                user=user,
                group=notification_data.get('group'),
                email_notifications=True
            ).first()
            
            if membership:
                self._send_email_notification(user, notification_data)
                
        except Exception as e:
            logger.error(f"Error sending notification to {user.email}: {e}")
    
    def _create_in_app_notification(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Create an in-app notification.
        
        Note: This would require a Notification model to be implemented.
        For now, we'll just log the notification.
        """
        notification_type = notification_data.get('type')
        group = notification_data.get('group')
        
        logger.info(f"In-app notification for {user.email}: {notification_type} in {group.name}")
        
        # TODO: Implement actual in-app notification storage
        # This would typically create a record in a Notification model
    
    def _send_email_notification(self, user: User, notification_data: Dict[str, Any]) -> None:
        """
        Send email notification to user.
        
        Args:
            user: User to send email to
            notification_data: Notification data
        """
        try:
            notification_type = notification_data.get('type')
            group = notification_data.get('group')
            
            # Prepare email content based on notification type
            subject, message = self._prepare_email_content(notification_type, notification_data)
            
            if subject and message:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    fail_silently=True  # Don't raise exceptions for email failures
                )
                
                logger.info(f"Sent email notification to {user.email}: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending email notification to {user.email}: {e}")
    
    def _prepare_email_content(
        self, 
        notification_type: str, 
        notification_data: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Prepare email subject and message based on notification type.
        
        Args:
            notification_type: Type of notification
            notification_data: Notification data
            
        Returns:
            Tuple of (subject, message)
        """
        group = notification_data.get('group')
        
        if notification_type == 'new_member_joined':
            new_member = notification_data.get('new_member')
            subject = f"New member joined {group.name}"
            message = f"{new_member.get_full_name()} has joined the {group.name} group."
            
        elif notification_type == 'new_post':
            post = notification_data.get('post')
            author = notification_data.get('author')
            subject = f"New post in {group.name}"
            message = f"{author.get_full_name()} posted '{post.title}' in {group.name}."
            
        elif notification_type == 'comment_on_post':
            post = notification_data.get('post')
            comment_author = notification_data.get('comment_author')
            subject = f"New comment on your post in {group.name}"
            message = f"{comment_author.get_full_name()} commented on your post '{post.title}' in {group.name}."
            
        elif notification_type == 'reply_to_comment':
            post = notification_data.get('post')
            comment_author = notification_data.get('comment_author')
            subject = f"Reply to your comment in {group.name}"
            message = f"{comment_author.get_full_name()} replied to your comment on '{post.title}' in {group.name}."
            
        elif notification_type == 'membership_request':
            requesting_user = notification_data.get('requesting_user')
            subject = f"New membership request for {group.name}"
            message = f"{requesting_user.get_full_name()} has requested to join {group.name}."
            
        elif notification_type == 'membership_approved':
            subject = f"Welcome to {group.name}!"
            message = f"Your request to join {group.name} has been approved. Welcome to the group!"
            
        elif notification_type == 'group_invitation':
            inviter = notification_data.get('inviter')
            subject = f"You've been invited to join {group.name}"
            message = f"{inviter.get_full_name()} has invited you to join the {group.name} group."
            
        else:
            subject = f"Update from {group.name}"
            message = f"There's a new update in the {group.name} group."
        
        return subject, message


# Global notification service instance
notification_service = GroupNotificationService()