"""
Django management command to set up MeiliSearch indexes.

Usage: python manage.py setup_search
"""

from django.core.management.base import BaseCommand
from koroh_platform.utils.meilisearch_client import setup_search_indexes


class Command(BaseCommand):
    help = 'Set up MeiliSearch indexes for the Koroh platform'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up MeiliSearch indexes...')
        )
        
        try:
            setup_search_indexes()
            self.stdout.write(
                self.style.SUCCESS('Successfully set up search indexes')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to set up search indexes: {e}')
            )