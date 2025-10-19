"""
Jobs app configuration.
"""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    """Configuration for the Jobs app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = 'Jobs'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import jobs.signals  # noqa F401
        except ImportError:
            pass