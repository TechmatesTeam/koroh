"""
Celery configuration for koroh_platform project.

This module configures Celery for background task processing,
including AWS Bedrock AI operations, email notifications,
and other asynchronous tasks.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')

app = Celery('koroh_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-job-recommendations': {
        'task': 'ai_services.tasks.update_job_recommendations',
        'schedule': 3600.0,  # Run every hour
    },
    'cleanup-expired-tokens': {
        'task': 'authentication.tasks.cleanup_expired_tokens',
        'schedule': 86400.0,  # Run daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')