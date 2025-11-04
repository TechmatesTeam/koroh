"""
Production health check endpoints for Koroh platform.
Provides comprehensive health monitoring for all system components.
"""

import json
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import redis
import requests
from celery import current_app as celery_app


def check_database():
    """Check database connectivity and performance."""
    try:
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'status': 'healthy',
            'response_time_ms': round(response_time, 2),
            'details': 'Database connection successful'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'Database connection failed'
        }


def check_redis():
    """Check Redis connectivity and performance."""
    try:
        start_time = time.time()
        cache.set('health_check', 'test', 10)
        result = cache.get('health_check')
        response_time = (time.time() - start_time) * 1000
        
        if result == 'test':
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'details': 'Redis connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'details': 'Redis read/write test failed'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'Redis connection failed'
        }


def check_celery():
    """Check Celery worker status."""
    try:
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            worker_count = len(active_workers)
            return {
                'status': 'healthy',
                'worker_count': worker_count,
                'workers': list(active_workers.keys()),
                'details': f'{worker_count} Celery workers active'
            }
        else:
            return {
                'status': 'unhealthy',
                'worker_count': 0,
                'details': 'No Celery workers active'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'Celery inspection failed'
        }


def check_meilisearch():
    """Check MeiliSearch connectivity."""
    try:
        meilisearch_url = getattr(settings, 'MEILISEARCH_URL', None)
        if not meilisearch_url:
            return {
                'status': 'disabled',
                'details': 'MeiliSearch not configured'
            }
        
        start_time = time.time()
        response = requests.get(f"{meilisearch_url}/health", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'details': 'MeiliSearch connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'status_code': response.status_code,
                'details': 'MeiliSearch health check failed'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'MeiliSearch connection failed'
        }


def check_aws_bedrock():
    """Check AWS Bedrock connectivity."""
    try:
        # Import here to avoid issues if boto3 is not available
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Create Bedrock client
        bedrock = boto3.client(
            'bedrock',
            region_name=getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1')
        )
        
        start_time = time.time()
        # List foundation models as a connectivity test
        response = bedrock.list_foundation_models()
        response_time = (time.time() - start_time) * 1000
        
        model_count = len(response.get('modelSummaries', []))
        
        return {
            'status': 'healthy',
            'response_time_ms': round(response_time, 2),
            'model_count': model_count,
            'details': 'AWS Bedrock connection successful'
        }
    except NoCredentialsError:
        return {
            'status': 'unhealthy',
            'error': 'AWS credentials not configured',
            'details': 'AWS Bedrock credentials missing'
        }
    except ClientError as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'AWS Bedrock client error'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'details': 'AWS Bedrock connection failed'
        }


def get_system_info():
    """Get system information."""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': getattr(settings, 'ENVIRONMENT', 'production'),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
    }


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns detailed status of all system components.
    """
    start_time = time.time()
    
    # Perform all health checks
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
        'meilisearch': check_meilisearch(),
        'aws_bedrock': check_aws_bedrock(),
    }
    
    # Determine overall status
    overall_status = 'healthy'
    unhealthy_services = []
    
    for service, check in checks.items():
        if check['status'] == 'unhealthy':
            overall_status = 'unhealthy'
            unhealthy_services.append(service)
        elif check['status'] == 'degraded' and overall_status == 'healthy':
            overall_status = 'degraded'
    
    # Calculate total response time
    total_response_time = (time.time() - start_time) * 1000
    
    # Build response
    response_data = {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'response_time_ms': round(total_response_time, 2),
        'system': get_system_info(),
        'services': checks,
    }
    
    if unhealthy_services:
        response_data['unhealthy_services'] = unhealthy_services
    
    # Set appropriate HTTP status code
    status_code = 200 if overall_status == 'healthy' else 503
    
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to receive traffic.
    """
    # Check critical services only
    critical_checks = {
        'database': check_database(),
        'redis': check_redis(),
    }
    
    # Service is ready if critical services are healthy
    ready = all(check['status'] == 'healthy' for check in critical_checks.values())
    
    response_data = {
        'ready': ready,
        'timestamp': datetime.utcnow().isoformat(),
        'critical_services': critical_checks,
    }
    
    status_code = 200 if ready else 503
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is alive and should not be restarted.
    """
    # Basic liveness check - just return success if Django is responding
    response_data = {
        'alive': True,
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': time.time() - getattr(settings, 'START_TIME', time.time()),
    }
    
    return JsonResponse(response_data, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def metrics_endpoint(request):
    """
    Prometheus-compatible metrics endpoint.
    Returns basic application metrics.
    """
    try:
        # Get database connection count
        db_connections = len(connection.queries) if settings.DEBUG else 0
        
        # Get cache stats
        cache_stats = cache.get_stats() if hasattr(cache, 'get_stats') else {}
        
        # Get Celery stats
        celery_stats = {}
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            celery_stats = {
                'active_workers': len(active_workers) if active_workers else 0,
                'active_tasks': sum(len(tasks) for tasks in active_workers.values()) if active_workers else 0,
            }
        except:
            pass
        
        metrics = {
            'koroh_app_info': {
                'version': getattr(settings, 'VERSION', '1.0.0'),
                'environment': getattr(settings, 'ENVIRONMENT', 'production'),
            },
            'koroh_db_connections_total': db_connections,
            'koroh_cache_hits_total': cache_stats.get('hits', 0),
            'koroh_cache_misses_total': cache_stats.get('misses', 0),
            'koroh_celery_workers_active': celery_stats.get('active_workers', 0),
            'koroh_celery_tasks_active': celery_stats.get('active_tasks', 0),
        }
        
        # Format as Prometheus metrics
        prometheus_output = []
        for metric_name, value in metrics.items():
            if isinstance(value, dict):
                # Handle info metrics
                labels = ','.join([f'{k}="{v}"' for k, v in value.items()])
                prometheus_output.append(f'{metric_name}{{{labels}}} 1')
            else:
                prometheus_output.append(f'{metric_name} {value}')
        
        return JsonResponse({
            'metrics': metrics,
            'prometheus_format': '\n'.join(prometheus_output)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, status=500)