"""
Companies app configuration.
"""

from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    """Configuration for the Companies app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'companies'
    verbose_name = 'Companies'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import companies.signals  # noqa F401
        except ImportError:
            pass