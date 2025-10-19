"""
Signal handlers for profiles app.

This module defines signal handlers for automatic profile creation
and other profile-related events.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a profile automatically when a new user is created.
    
    This signal handler ensures every user has a profile.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user's profile when the user is saved.
    
    This ensures the profile exists and is kept in sync.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist
        Profile.objects.create(user=instance)