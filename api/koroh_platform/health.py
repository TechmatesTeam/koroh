"""
Health check endpoints for production deployment.

Requirements: 4.1, 4.2, 7.1, 7.2
"""

import logging
import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def health_check(request):
    """
    Basic health check endpoint for load balancers.
    Returns 200 if the service is running.
    """
    return Response({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'koroh-api'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def readiness_check(request):
    """
    Readiness check endpoint that validates all dependencies.
    Returns 200 only if all required services are available.
    """
    checks = {
        'database': False,
        'cache': False,
        'overall': False
    }
    
    errors = []
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks['database'] = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logger.error(f"Database health check failed: {e}")
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 10)
        cached_value = cache.get(cache_key)
        if cached_value == 'test_value':
            checks['cache'] = True
            cache.delete(cache_key)
        else:
            errors.append("Cache read/write test failed")
    except Exception as e:
        errors.append(f"Cache error: {str(e)}")
        logger.error(f"Cache health check failed: {e}")
    
    # Overall status
    checks['overall'] = all([checks['database'], checks['cache']])
    
    response_data = {
        'status': 'ready' if checks['overall'] else 'not_ready',
        'checks': checks,
        'timestamp': time.time(),
        'service': 'koroh-api'
    }
    
    if errors:
        response_data['errors'] = errors
    
    response_status = status.HTTP_200_OK if checks['overall'] else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(response_data, status=response_status)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def liveness_check(request):
    """
    Liveness check endpoint for Kubernetes.
    Returns 200 if the application is alive and can handle requests.
    """
    try:
        # Basic application liveness test
        # Check if we can import core modules
        from django.contrib.auth.models import User
        from profiles.models import Profile
        
        return Response({
            'status': 'alive',
            'timestamp': time.time(),
            'service': 'koroh-api',
            'version': getattr(settings, 'VERSION', '1.0.0')
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return Response({
            'status': 'dead',
            'error': str(e),
            'timestamp': time.time(),
            'service': 'koroh-api'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def detailed_status(request):
    """
    Detailed status endpoint for monitoring and debugging.
    Provides comprehensive system status information.
    """
    status_info = {
        'service': 'koroh-api',
        'timestamp': time.time(),
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': 'production' if not settings.DEBUG else 'development',
        'checks': {}
    }
    
    # Database status
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
            
        status_info['checks']['database'] = {
            'status': 'healthy',
            'version': db_version,
            'migrations': migration_count
        }
    except Exception as e:
        status_info['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Cache status
    try:
        cache_key = 'detailed_status_test'
        test_start = time.time()
        cache.set(cache_key, 'test_value', 10)
        cached_value = cache.get(cache_key)
        test_duration = time.time() - test_start
        cache.delete(cache_key)
        
        status_info['checks']['cache'] = {
            'status': 'healthy' if cached_value == 'test_value' else 'unhealthy',
            'response_time_ms': round(test_duration * 1000, 2)
        }
    except Exception as e:
        status_info['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # AI Services status (basic check)
    try:
        from koroh_platform.utils.aws_bedrock import BedrockClient
        bedrock_client = BedrockClient()
        
        status_info['checks']['ai_services'] = {
            'status': 'configured' if bedrock_client else 'not_configured',
            'available': bedrock_client.is_available() if bedrock_client else False
        }
    except Exception as e:
        status_info['checks']['ai_services'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Celery status (if available)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_tasks = inspect.active()
        
        status_info['checks']['celery'] = {
            'status': 'healthy' if active_tasks is not None else 'unhealthy',
            'workers': list(active_tasks.keys()) if active_tasks else []
        }
    except Exception as e:
        status_info['checks']['celery'] = {
            'status': 'unavailable',
            'error': str(e)
        }
    
    # Overall status
    healthy_checks = sum(1 for check in status_info['checks'].values() 
                        if check.get('status') in ['healthy', 'configured'])
    total_checks = len(status_info['checks'])
    
    status_info['overall'] = {
        'status': 'healthy' if healthy_checks >= total_checks * 0.75 else 'degraded',
        'healthy_checks': healthy_checks,
        'total_checks': total_checks
    }
    
    response_status = status.HTTP_200_OK if status_info['overall']['status'] == 'healthy' else status.HTTP_206_PARTIAL_CONTENT
    
    return Response(status_info, status=response_status)


@require_http_methods(["GET"])
@never_cache
def metrics_endpoint(request):
    """
    Prometheus metrics endpoint.
    """
    try:
        from django_prometheus.exports import ExportToDjangoView
        return ExportToDjangoView(request)
    except ImportError:
        return JsonResponse({
            'error': 'Prometheus metrics not available'
        }, status=503)