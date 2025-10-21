"""
Django management command to collect and update custom metrics.

This command can be run periodically to update gauge metrics
that require database queries or system checks.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from koroh_platform.utils.metrics import (
    update_active_users_count,
    update_celery_queue_size,
    track_feature_usage
)

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Collect and update custom Prometheus metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Collection interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run collection once and exit'
        )

    def handle(self, *args, **options):
        """Handle the metrics collection command."""
        
        self.stdout.write(
            self.style.SUCCESS('Starting metrics collection...')
        )
        
        try:
            self.collect_user_metrics()
            self.collect_celery_metrics()
            self.collect_application_metrics()
            
            self.stdout.write(
                self.style.SUCCESS('Metrics collection completed successfully')
            )
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Metrics collection failed: {e}')
            )
            raise

    def collect_user_metrics(self):
        """Collect user-related metrics."""
        
        try:
            # Count active users (logged in within last 24 hours)
            last_24_hours = timezone.now() - timedelta(hours=24)
            active_users = User.objects.filter(
                last_login__gte=last_24_hours
            ).count()
            
            update_active_users_count(active_users)
            
            self.stdout.write(f'Updated active users count: {active_users}')
            
        except Exception as e:
            logger.error(f"Failed to collect user metrics: {e}")
            raise

    def collect_celery_metrics(self):
        """Collect Celery task queue metrics."""
        
        try:
            # This would require celery inspection
            # For now, we'll set a placeholder
            # In production, you'd use celery.control.inspect()
            
            # Example implementation:
            # from celery import current_app
            # inspect = current_app.control.inspect()
            # active_tasks = inspect.active()
            # scheduled_tasks = inspect.scheduled()
            
            # For now, set to 0 as placeholder
            update_celery_queue_size('default', 0)
            update_celery_queue_size('ai_tasks', 0)
            
            self.stdout.write('Updated Celery queue metrics')
            
        except Exception as e:
            logger.error(f"Failed to collect Celery metrics: {e}")
            # Don't raise here as Celery might not be running

    def collect_application_metrics(self):
        """Collect application-specific metrics."""
        
        try:
            from profiles.models import Profile
            from jobs.models import Job
            from companies.models import Company
            from peer_groups.models import PeerGroup
            
            # Count total profiles with CVs
            profiles_with_cv = Profile.objects.exclude(cv_file='').count()
            
            # Count active jobs
            active_jobs = Job.objects.filter(is_active=True).count()
            
            # Count companies
            total_companies = Company.objects.count()
            
            # Count peer groups
            total_peer_groups = PeerGroup.objects.count()
            
            # Track these as feature usage metrics
            track_feature_usage('profiles_with_cv', 'system')
            track_feature_usage('active_jobs', 'system')
            track_feature_usage('total_companies', 'system')
            track_feature_usage('total_peer_groups', 'system')
            
            self.stdout.write(
                f'Application metrics - Profiles with CV: {profiles_with_cv}, '
                f'Active jobs: {active_jobs}, Companies: {total_companies}, '
                f'Peer groups: {total_peer_groups}'
            )
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            # Don't raise here as models might not be available