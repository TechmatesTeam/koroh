"""
App configuration for profiles app.

This module defines the app configuration and signal handlers
for the profiles application.
"""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Configuration for profiles app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'
    verbose_name = 'User Profiles'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        import profiles.signals