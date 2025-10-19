"""
Signals for peer groups app.

This module defines Django signals for peer group models to handle
automatic updates and notifications.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import GroupMembership, GroupPost, GroupComment
from .notifications import notification_service


@receiver(post_save, sender=GroupMembership)
def update_group_member_count_on_save(sender, instance, created, **kwargs):
    """Update group member count when membership is saved."""
    if created or instance.status in ['active', 'left', 'banned']:
        instance.group.update_member_count()


@receiver(post_delete, sender=GroupMembership)
def update_group_member_count_on_delete(sender, instance, **kwargs):
    """Update group member count when membership is deleted."""
    instance.group.update_member_count()


@receiver(post_save, sender=GroupPost)
def update_group_activity_on_post(sender, instance, created, **kwargs):
    """Update group activity when a post is created."""
    if created:
        instance.group.update_last_activity()
        instance.group.update_activity_score()


@receiver(post_save, sender=GroupComment)
def update_group_activity_on_comment(sender, instance, created, **kwargs):
    """Update group activity when a comment is created."""
    if created:
        instance.post.group.update_last_activity()
        instance.post.group.update_activity_score()


@receiver(post_save, sender=GroupMembership)
def update_member_activity(sender, instance, **kwargs):
    """Update member's last activity timestamp."""
    if instance.status == 'active':
        instance.update_activity()


# Notification signals
@receiver(post_save, sender=GroupMembership)
def send_membership_notifications(sender, instance, created, **kwargs):
    """Send notifications for membership changes."""
    if created:
        if instance.status == 'active':
            # New member joined
            notification_service.notify_new_member_joined(instance)
        elif instance.status == 'pending':
            # Membership request
            notification_service.notify_membership_request(instance)
        elif instance.status == 'invited':
            # Group invitation
            notification_service.notify_group_invitation(instance)
    else:
        # Status changed
        if instance.status == 'active':
            # Membership approved
            notification_service.notify_membership_approved(instance)


@receiver(post_save, sender=GroupPost)
def send_new_post_notifications(sender, instance, created, **kwargs):
    """Send notifications for new posts."""
    if created:
        notification_service.notify_new_post(instance)


@receiver(post_save, sender=GroupComment)
def send_new_comment_notifications(sender, instance, created, **kwargs):
    """Send notifications for new comments."""
    if created:
        notification_service.notify_new_comment(instance)