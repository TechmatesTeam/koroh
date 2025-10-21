"""
Custom middleware for security, performance, and caching optimizations.

Requirements: 4.3, 4.4, 4.5
"""

import time
import logging
from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.middleware.security import SecurityMiddleware as DjangoSecurityMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add comprehensive security headers to all responses.
    
    Requirements: 4.4, 4.5
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.koroh.dev wss://api.koroh.dev",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS (only in production with HTTPS)
        if settings.DEBUG is False and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        
        return response


class PerformanceMiddleware(MiddlewareMixin):
    """
    Performance monitoring and optimization middleware.
    
    Requirements: 4.3, 4.4
    """
    
    def process_request(self, request):
        """Start performance timing."""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Add performance headers and logging."""
        
        # Calculate response time
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Log slow requests
            if response_time > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {response_time:.3f}s"
                )
        
        # Add cache control headers for static content
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        
        # Add cache headers for API responses
        elif request.path.startswith('/api/'):
            if request.method == 'GET' and response.status_code == 200:
                # Cache GET requests for 5 minutes by default
                response['Cache-Control'] = 'private, max-age=300'
            else:
                # Don't cache non-GET requests or error responses
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse.
    
    Requirements: 4.4, 4.5
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check rate limits for the request."""
        
        # Skip rate limiting for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Skip rate limiting in debug mode for testing
        if settings.DEBUG:
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Different rate limits for different endpoints
        rate_limits = {
            '/api/v1/auth/login/': (10, 300),  # 10 attempts per 5 minutes (increased for testing)
            '/api/v1/auth/register/': (5, 3600),  # 5 attempts per hour (increased for testing)
            '/api/v1/ai/send/': (50, 60),  # 50 AI requests per minute for authenticated users
            '/api/v1/ai/anonymous/': (20, 3600),  # 20 anonymous requests per hour
            '/api/v1/profiles/upload-cv/': (10, 3600),  # 10 uploads per hour
            '/api/v1/profiles/generate-portfolio/': (10, 3600),  # 10 portfolio generations per hour
        }
        
        # Check specific endpoint limits
        for endpoint, (limit, window) in rate_limits.items():
            if request.path.startswith(endpoint):
                if self.is_rate_limited(client_ip, endpoint, limit, window):
                    return HttpResponse(
                        '{"error": "Rate limit exceeded. Please try again later."}',
                        status=429,
                        content_type='application/json'
                    )
        
        # General API rate limit (exclude anonymous chat which has its own limits)
        if request.path.startswith('/api/') and not request.path.startswith('/api/v1/ai/anonymous/'):
            if self.is_rate_limited(client_ip, 'api_general', 200, 3600):  # 200 per hour (increased for testing)
                return HttpResponse(
                    '{"error": "API rate limit exceeded. Please try again later."}',
                    status=429,
                    content_type='application/json'
                )
        
        return None
    
    def get_client_ip(self, request):
        """Get the client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, client_ip, endpoint, limit, window):
        """Check if the client has exceeded the rate limit."""
        cache_key = f"rate_limit:{client_ip}:{endpoint}"
        
        try:
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= limit:
                return True
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, window)
            return False
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - don't block requests if cache is down
            return False


class CacheOptimizationMiddleware(MiddlewareMixin):
    """
    Intelligent caching middleware for API responses.
    
    Requirements: 4.3
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Define cacheable endpoints and their TTL
        self.cache_config = {
            '/api/v1/jobs/search/': 300,  # 5 minutes
            '/api/v1/companies/search/': 600,  # 10 minutes
            '/api/v1/groups/discover/': 300,  # 5 minutes
            '/api/v1/profiles/portfolios/': 1800,  # 30 minutes
        }
    
    def process_request(self, request):
        """Check if we have a cached response."""
        
        # Only cache GET requests
        if request.method != 'GET':
            return None
        
        # Check if this endpoint should be cached
        cache_ttl = self.get_cache_ttl(request.path)
        if not cache_ttl:
            return None
        
        # Generate cache key
        cache_key = self.generate_cache_key(request)
        
        try:
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.path}")
                response = HttpResponse(
                    cached_response['content'],
                    status=cached_response['status'],
                    content_type=cached_response['content_type']
                )
                response['X-Cache'] = 'HIT'
                return response
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    def process_response(self, request, response):
        """Cache successful GET responses."""
        
        # Only cache successful GET requests
        if request.method != 'GET' or response.status_code != 200:
            return response
        
        # Check if this endpoint should be cached
        cache_ttl = self.get_cache_ttl(request.path)
        if not cache_ttl:
            return response
        
        # Don't cache if user is authenticated (for personalized content)
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Only cache non-personalized endpoints for authenticated users
            if not self.is_personalizable_endpoint(request.path):
                cache_ttl = cache_ttl // 2  # Reduce TTL for authenticated users
            else:
                return response
        
        # Generate cache key and store response
        cache_key = self.generate_cache_key(request)
        
        try:
            cached_data = {
                'content': response.content.decode('utf-8'),
                'status': response.status_code,
                'content_type': response.get('Content-Type', 'application/json')
            }
            cache.set(cache_key, cached_data, cache_ttl)
            response['X-Cache'] = 'MISS'
            logger.debug(f"Cached response for {request.path}")
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
        
        return response
    
    def get_cache_ttl(self, path):
        """Get cache TTL for a given path."""
        for endpoint, ttl in self.cache_config.items():
            if path.startswith(endpoint):
                return ttl
        return None
    
    def generate_cache_key(self, request):
        """Generate a cache key for the request."""
        # Include query parameters in cache key
        query_string = request.META.get('QUERY_STRING', '')
        user_id = getattr(request.user, 'id', 'anonymous') if hasattr(request, 'user') else 'anonymous'
        
        return f"api_cache:{request.path}:{query_string}:{user_id}"
    
    def is_personalizable_endpoint(self, path):
        """Check if endpoint returns personalized content."""
        personalized_endpoints = [
            '/api/v1/profiles/me/',
            '/api/v1/jobs/recommendations/',
            '/api/v1/groups/my-groups/',
            '/api/v1/ai/chat/'
        ]
        
        return any(path.startswith(endpoint) for endpoint in personalized_endpoints)


class CompressionMiddleware(MiddlewareMixin):
    """
    Response compression middleware for better performance.
    
    Requirements: 4.3
    """
    
    def process_response(self, request, response):
        """Add compression hints and optimize response size."""
        
        # Add compression headers for compressible content
        content_type = response.get('Content-Type', '')
        
        if any(ct in content_type for ct in ['application/json', 'text/', 'application/javascript']):
            response['Vary'] = 'Accept-Encoding'
            
            # Hint that this content should be compressed
            if not response.get('Content-Encoding'):
                response['X-Compress-Hint'] = 'true'
        
        # Optimize JSON responses
        if 'application/json' in content_type and hasattr(response, 'content'):
            try:
                # Remove unnecessary whitespace from JSON (if not already minified)
                import json
                content = response.content.decode('utf-8')
                if '  ' in content or '\n' in content:  # Has formatting
                    data = json.loads(content)
                    minified = json.dumps(data, separators=(',', ':'))
                    response.content = minified.encode('utf-8')
                    response['Content-Length'] = str(len(response.content))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If it's not valid JSON, leave it as is
                pass
        
        return response


class DatabaseOptimizationMiddleware(MiddlewareMixin):
    """
    Database query optimization and monitoring middleware.
    
    Requirements: 4.3
    """
    
    def process_request(self, request):
        """Initialize database query tracking."""
        if settings.DEBUG:
            from django.db import connection
            request._db_queries_start = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Log database query information."""
        
        if settings.DEBUG and hasattr(request, '_db_queries_start'):
            from django.db import connection
            
            query_count = len(connection.queries) - request._db_queries_start
            
            # Log excessive database queries
            if query_count > 10:
                logger.warning(
                    f"High DB query count: {request.method} {request.path} "
                    f"executed {query_count} queries"
                )
            
            # Add query count to response headers in debug mode
            response['X-DB-Queries'] = str(query_count)
        
        return response


class CORSMiddleware(MiddlewareMixin):
    """
    CORS middleware with security-focused configuration.
    
    Requirements: 4.4, 4.5
    """
    
    def process_request(self, request):
        """Handle preflight requests."""
        if request.method == 'OPTIONS':
            from django.http import HttpResponse
            response = HttpResponse()
            response.status_code = 200
            return self.add_cors_headers(request, response)
        return None
    
    def process_response(self, request, response):
        """Add CORS headers with security considerations."""
        return self.add_cors_headers(request, response)
    
    def add_cors_headers(self, request, response):
        """Add CORS headers to response."""
        # Get allowed origins from settings
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        
        origin = request.META.get('HTTP_ORIGIN')
        
        if origin and origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
        elif settings.DEBUG:
            # In development, allow localhost origins
            if origin and ('localhost' in origin or '127.0.0.1' in origin):
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
        
        # Always add these headers for preflight and actual requests
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'Accept, Accept-Language, Content-Language, Content-Type, '
            'Authorization, X-Requested-With, X-CSRFToken, Origin'
        )
        response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response