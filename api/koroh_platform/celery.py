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
    # AI and recommendation tasks
    'update-job-recommendations': {
        'task': 'koroh_platform.tasks.update_job_recommendations',
        'schedule': 3600.0,  # Run every hour
    },
    'update-peer-group-recommendations': {
        'task': 'koroh_platform.tasks.update_peer_group_recommendations',
        'schedule': 7200.0,  # Run every 2 hours
    },
    'send-weekly-job-digest': {
        'task': 'koroh_platform.tasks.send_weekly_job_digest',
        'schedule': 604800.0,  # Run weekly (7 days)
    },
    'cleanup-ai-processing-data': {
        'task': 'koroh_platform.tasks.cleanup_ai_processing_data',
        'schedule': 86400.0,  # Run daily
    },
    'monitor-ai-service-health': {
        'task': 'koroh_platform.tasks.monitor_ai_service_health',
        'schedule': 900.0,  # Run every 15 minutes
    },
    
    # Authentication and user management tasks
    'cleanup-expired-tokens': {
        'task': 'authentication.tasks.cleanup_expired_tokens',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-inactive-users': {
        'task': 'authentication.tasks.cleanup_inactive_users',
        'schedule': 86400.0,  # Run daily
    },
    
    # Profile and file management tasks
    'cleanup-orphaned-files': {
        'task': 'profiles.tasks.cleanup_orphaned_files',
        'schedule': 604800.0,  # Run weekly
    },
    
    # Company and job tasks
    'update-all-company-insights': {
        'task': 'companies.tasks.update_all_company_insights',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-expired-insights': {
        'task': 'companies.tasks.cleanup_expired_insights',
        'schedule': 86400.0,  # Run daily
    },
    'send-weekly-digests': {
        'task': 'companies.tasks.send_weekly_digests',
        'schedule': 604800.0,  # Run weekly
    },
}

app.conf.timezone = 'UTC'

# Enhanced Celery configuration for better monitoring and error handling
app.conf.update(
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        'koroh_platform.tasks.*': {'queue': 'ai_processing'},
        'authentication.tasks.*': {'queue': 'user_management'},
        'profiles.tasks.*': {'queue': 'file_processing'},
        'companies.tasks.*': {'queue': 'notifications'},
        'jobs.tasks.*': {'queue': 'recommendations'},
        'peer_groups.tasks.*': {'queue': 'notifications'},
    },
    
    # Task time limits
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_annotations={
        '*': {
            'rate_limit': '100/m',  # Default rate limit
            'time_limit': 300,
            'soft_time_limit': 240,
        },
        'koroh_platform.tasks.analyze_cv_with_ai': {
            'rate_limit': '10/m',  # Limit AI tasks
            'time_limit': 600,  # 10 minutes for CV analysis
            'soft_time_limit': 540,
        },
        'koroh_platform.tasks.generate_portfolio_with_ai': {
            'rate_limit': '10/m',
            'time_limit': 600,
            'soft_time_limit': 540,
        },
        'koroh_platform.tasks.update_job_recommendations': {
            'rate_limit': '5/m',
            'time_limit': 900,  # 15 minutes for batch processing
            'soft_time_limit': 840,
        },
        'koroh_platform.tasks.update_peer_group_recommendations': {
            'rate_limit': '5/m',
            'time_limit': 900,  # 15 minutes for batch processing
            'soft_time_limit': 840,
        },
    }
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')