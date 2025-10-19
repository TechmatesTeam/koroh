"""
App configuration for peer groups.

This module defines the Django app configuration for the peer groups app.
"""

from django.apps import AppConfig


class PeerGroupsConfig(AppConfig):
    """Configuration for the peer groups app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'peer_groups'
    verbose_name = 'Peer Groups'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import peer_groups.signals  # noqa F401
        except ImportError:
            pass