"""
URL configuration for koroh_platform project.

Main URL routing for the Koroh platform API.
Includes versioned API endpoints and admin interface.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import health
from django.http import HttpResponse

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API v1 endpoints
    path('api/v1/', include([
        # Authentication endpoints
        path('auth/', include('authentication.urls')),
        
        # Core app endpoints
        path('profiles/', include('profiles.urls')),
        path('jobs/', include('jobs.urls')),
        path('companies/', include('companies.urls')),
        path('peer_groups/', include('peer_groups.urls')),
        path('', include('peer_groups.urls')),  # Keep backward compatibility
        path('ai/', include('ai_chat.urls')),
    ])),
    
    # Health check endpoints
    path('health/', health.health_check, name='health_check'),
    path('health/ready/', health.readiness_check, name='readiness_check'),
    path('health/live/', health.liveness_check, name='liveness_check'),
    path('api/v1/health/', health.health_check, name='api_health_check'),
    
    # Prometheus metrics endpoint
    path('metrics/', include('django_prometheus.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
