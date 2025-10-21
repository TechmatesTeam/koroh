"""
Custom Prometheus metrics for Koroh platform.

This module defines custom metrics for monitoring AI service usage,
user activities, and business-specific metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from django.conf import settings

# AI Service Metrics
ai_requests_total = Counter(
    'koroh_ai_requests_total',
    'Total number of AI service requests',
    ['service_type', 'model', 'status']
)

ai_request_duration = Histogram(
    'koroh_ai_request_duration_seconds',
    'Time spent on AI service requests',
    ['service_type', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

ai_tokens_used = Counter(
    'koroh_ai_tokens_used_total',
    'Total number of AI tokens consumed',
    ['service_type', 'model', 'token_type']
)

# User Activity Metrics
user_registrations_total = Counter(
    'koroh_user_registrations_total',
    'Total number of user registrations'
)

cv_uploads_total = Counter(
    'koroh_cv_uploads_total',
    'Total number of CV uploads',
    ['file_type', 'status']
)

portfolio_generations_total = Counter(
    'koroh_portfolio_generations_total',
    'Total number of portfolio generations',
    ['template_type', 'status']
)

job_searches_total = Counter(
    'koroh_job_searches_total',
    'Total number of job searches',
    ['search_type']
)

peer_group_activities_total = Counter(
    'koroh_peer_group_activities_total',
    'Total peer group activities',
    ['activity_type']
)

# System Health Metrics
active_users_gauge = Gauge(
    'koroh_active_users',
    'Number of currently active users'
)

celery_tasks_pending = Gauge(
    'koroh_celery_tasks_pending',
    'Number of pending Celery tasks',
    ['queue_name']
)

celery_tasks_processed = Counter(
    'koroh_celery_tasks_processed_total',
    'Total number of processed Celery tasks',
    ['task_name', 'status']
)

# Business Metrics
revenue_metrics = Counter(
    'koroh_revenue_total',
    'Total revenue generated',
    ['revenue_type', 'currency']
)

feature_usage = Counter(
    'koroh_feature_usage_total',
    'Feature usage statistics',
    ['feature_name', 'user_type']
)

# Application Info
app_info = Info(
    'koroh_app_info',
    'Application information'
)

# Set application info
app_info.info({
    'version': getattr(settings, 'APP_VERSION', '1.0.0'),
    'environment': 'development' if settings.DEBUG else 'production',
    'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown')
})


def track_ai_request(service_type, model_name=None):
    """
    Decorator to track AI service requests.
    
    Args:
        service_type: Type of AI service (cv_analysis, portfolio_generation, etc.)
        model_name: Name of the AI model used
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            model = model_name or getattr(settings, 'AWS_BEDROCK_DEFAULT_MODEL', 'unknown')
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                ai_requests_total.labels(
                    service_type=service_type,
                    model=model,
                    status='success'
                ).inc()
                
                # Track token usage if available in result
                if isinstance(result, dict) and 'token_usage' in result:
                    token_usage = result['token_usage']
                    if 'input_tokens' in token_usage:
                        ai_tokens_used.labels(
                            service_type=service_type,
                            model=model,
                            token_type='input'
                        ).inc(token_usage['input_tokens'])
                    if 'output_tokens' in token_usage:
                        ai_tokens_used.labels(
                            service_type=service_type,
                            model=model,
                            token_type='output'
                        ).inc(token_usage['output_tokens'])
                
                return result
                
            except Exception as e:
                ai_requests_total.labels(
                    service_type=service_type,
                    model=model,
                    status='error'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                ai_request_duration.labels(
                    service_type=service_type,
                    model=model
                ).observe(duration)
        
        return wrapper
    return decorator


def track_user_activity(activity_type):
    """
    Decorator to track user activities.
    
    Args:
        activity_type: Type of user activity
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Track specific activities
                if activity_type == 'cv_upload':
                    file_type = kwargs.get('file_type', 'unknown')
                    cv_uploads_total.labels(
                        file_type=file_type,
                        status='success'
                    ).inc()
                elif activity_type == 'portfolio_generation':
                    template_type = kwargs.get('template_type', 'default')
                    portfolio_generations_total.labels(
                        template_type=template_type,
                        status='success'
                    ).inc()
                elif activity_type == 'job_search':
                    search_type = kwargs.get('search_type', 'general')
                    job_searches_total.labels(search_type=search_type).inc()
                elif activity_type.startswith('peer_group_'):
                    peer_group_activities_total.labels(
                        activity_type=activity_type
                    ).inc()
                
                return result
                
            except Exception as e:
                # Track failed activities
                if activity_type == 'cv_upload':
                    file_type = kwargs.get('file_type', 'unknown')
                    cv_uploads_total.labels(
                        file_type=file_type,
                        status='error'
                    ).inc()
                elif activity_type == 'portfolio_generation':
                    template_type = kwargs.get('template_type', 'default')
                    portfolio_generations_total.labels(
                        template_type=template_type,
                        status='error'
                    ).inc()
                raise
        
        return wrapper
    return decorator


def track_celery_task(task_name):
    """
    Decorator to track Celery task execution.
    
    Args:
        task_name: Name of the Celery task
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                celery_tasks_processed.labels(
                    task_name=task_name,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                celery_tasks_processed.labels(
                    task_name=task_name,
                    status='error'
                ).inc()
                raise
        
        return wrapper
    return decorator


def update_active_users_count(count):
    """Update the active users gauge."""
    active_users_gauge.set(count)


def update_celery_queue_size(queue_name, size):
    """Update the Celery queue size gauge."""
    celery_tasks_pending.labels(queue_name=queue_name).set(size)


def track_feature_usage(feature_name, user_type='regular'):
    """Track feature usage."""
    feature_usage.labels(
        feature_name=feature_name,
        user_type=user_type
    ).inc()


def track_revenue(amount, revenue_type='subscription', currency='USD'):
    """Track revenue metrics."""
    revenue_metrics.labels(
        revenue_type=revenue_type,
        currency=currency
    ).inc(amount)