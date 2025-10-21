"""
Performance optimization utilities for the Koroh platform.

Requirements: 4.3, 4.4
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.db.models import QuerySet, Prefetch
from django.db.models.query import Q

logger = logging.getLogger(__name__)


def cache_result(timeout: int = 300, key_prefix: str = '', vary_on: List[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        vary_on: List of argument names to include in cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            
            if vary_on:
                for arg_name in vary_on:
                    if arg_name in kwargs:
                        cache_key_parts.append(f"{arg_name}:{kwargs[arg_name]}")
            
            cache_key = ':'.join(str(part) for part in cache_key_parts)
            
            # Try to get from cache
            try:
                result = cache.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return result
            except Exception as e:
                logger.error(f"Cache retrieval error for {cache_key}: {e}")
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            try:
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cached result for {cache_key}")
            except Exception as e:
                logger.error(f"Cache storage error for {cache_key}: {e}")
            
            return result
        return wrapper
    return decorator


def monitor_db_queries(func: Callable) -> Callable:
    """
    Decorator to monitor database queries for a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if settings.DEBUG:
            initial_queries = len(connection.queries)
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            query_count = len(connection.queries) - initial_queries
            execution_time = end_time - start_time
            
            if query_count > 5 or execution_time > 1.0:
                logger.warning(
                    f"Performance warning: {func.__name__} executed {query_count} "
                    f"queries in {execution_time:.3f}s"
                )
            
            return result
        else:
            return func(*args, **kwargs)
    return wrapper


class QueryOptimizer:
    """
    Utility class for optimizing database queries.
    """
    
    @staticmethod
    def optimize_queryset(queryset: QuerySet, select_related: List[str] = None, 
                         prefetch_related: List[str] = None) -> QuerySet:
        """
        Optimize a queryset with select_related and prefetch_related.
        
        Args:
            queryset: The queryset to optimize
            select_related: List of fields for select_related
            prefetch_related: List of fields for prefetch_related
        
        Returns:
            Optimized queryset
        """
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset
    
    @staticmethod
    def get_user_profile_optimized(user_id: int):
        """
        Get user profile with optimized queries.
        """
        from profiles.models import Profile
        
        return Profile.objects.select_related('user').prefetch_related(
            'user__groups',
            'portfolios'
        ).get(user_id=user_id)
    
    @staticmethod
    def get_jobs_with_companies(filters: Dict[str, Any] = None) -> QuerySet:
        """
        Get jobs with company information using optimized queries.
        """
        from jobs.models import Job
        
        queryset = Job.objects.select_related('company').prefetch_related(
            'company__followers',
            'applications'
        )
        
        if filters:
            filter_q = Q()
            for field, value in filters.items():
                if field == 'title':
                    filter_q &= Q(title__icontains=value)
                elif field == 'location':
                    filter_q &= Q(location__icontains=value)
                elif field == 'company':
                    filter_q &= Q(company__name__icontains=value)
                elif field == 'skills':
                    filter_q &= Q(requirements__overlap=value)
            
            queryset = queryset.filter(filter_q)
        
        return queryset.order_by('-posted_date')
    
    @staticmethod
    def get_peer_groups_with_members(user_id: int = None) -> QuerySet:
        """
        Get peer groups with member information using optimized queries.
        """
        from peer_groups.models import PeerGroup
        
        queryset = PeerGroup.objects.select_related('created_by').prefetch_related(
            'members',
            'groupmembership_set__user'
        )
        
        if user_id:
            # Get groups the user is not already a member of
            queryset = queryset.exclude(members__id=user_id)
        
        return queryset.order_by('-created_at')


class CacheManager:
    """
    Centralized cache management for the application.
    """
    
    # Cache key patterns
    USER_PROFILE_KEY = "user_profile:{user_id}"
    JOB_RECOMMENDATIONS_KEY = "job_recommendations:{user_id}"
    PEER_GROUP_SUGGESTIONS_KEY = "peer_suggestions:{user_id}"
    COMPANY_INSIGHTS_KEY = "company_insights:{company_id}"
    CV_ANALYSIS_KEY = "cv_analysis:{cv_hash}"
    PORTFOLIO_CONTENT_KEY = "portfolio_content:{user_id}:{template}"
    
    @classmethod
    def get_user_profile(cls, user_id: int) -> Optional[Dict]:
        """Get cached user profile."""
        cache_key = cls.USER_PROFILE_KEY.format(user_id=user_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_user_profile(cls, user_id: int, profile_data: Dict, timeout: int = 1800):
        """Cache user profile data."""
        cache_key = cls.USER_PROFILE_KEY.format(user_id=user_id)
        cache.set(cache_key, profile_data, timeout)
    
    @classmethod
    def invalidate_user_profile(cls, user_id: int):
        """Invalidate cached user profile."""
        cache_key = cls.USER_PROFILE_KEY.format(user_id=user_id)
        cache.delete(cache_key)
    
    @classmethod
    def get_job_recommendations(cls, user_id: int) -> Optional[List]:
        """Get cached job recommendations."""
        cache_key = cls.JOB_RECOMMENDATIONS_KEY.format(user_id=user_id)
        return cache.get(cache_key)
    
    @classmethod
    def set_job_recommendations(cls, user_id: int, recommendations: List, timeout: int = 3600):
        """Cache job recommendations."""
        cache_key = cls.JOB_RECOMMENDATIONS_KEY.format(user_id=user_id)
        cache.set(cache_key, recommendations, timeout)
    
    @classmethod
    def get_cv_analysis(cls, cv_hash: str) -> Optional[Dict]:
        """Get cached CV analysis results."""
        cache_key = cls.CV_ANALYSIS_KEY.format(cv_hash=cv_hash)
        return cache.get(cache_key)
    
    @classmethod
    def set_cv_analysis(cls, cv_hash: str, analysis_data: Dict, timeout: int = 86400):
        """Cache CV analysis results."""
        cache_key = cls.CV_ANALYSIS_KEY.format(cv_hash=cv_hash)
        cache.set(cache_key, analysis_data, timeout)
    
    @classmethod
    def bulk_invalidate(cls, pattern: str):
        """Invalidate multiple cache keys matching a pattern."""
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            keys = redis_conn.keys(f"koroh:{pattern}*")
            if keys:
                redis_conn.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching {pattern}")
        except Exception as e:
            logger.error(f"Bulk cache invalidation failed: {e}")


class PerformanceProfiler:
    """
    Performance profiling utilities.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.db_queries_start = None
    
    def __enter__(self):
        self.start_time = time.time()
        if settings.DEBUG:
            self.db_queries_start = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        log_data = {
            'operation': self.name,
            'execution_time': f"{execution_time:.3f}s"
        }
        
        if settings.DEBUG and self.db_queries_start is not None:
            query_count = len(connection.queries) - self.db_queries_start
            log_data['db_queries'] = query_count
            
            if query_count > 10:
                log_data['warning'] = 'High query count'
        
        if execution_time > 1.0:
            logger.warning(f"Slow operation: {log_data}")
        else:
            logger.debug(f"Performance: {log_data}")


def optimize_ai_service_calls():
    """
    Decorator to optimize AI service calls with caching and retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract cache key from arguments
            cache_key = f"ai_service:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            try:
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.debug(f"AI service cache hit: {func.__name__}")
                    return cached_result
            except Exception as e:
                logger.error(f"AI service cache error: {e}")
            
            # Execute with performance monitoring
            with PerformanceProfiler(f"ai_service_{func.__name__}"):
                result = func(*args, **kwargs)
            
            # Cache successful results
            if result and not isinstance(result, Exception):
                try:
                    cache.set(cache_key, result, 3600)  # Cache for 1 hour
                    logger.debug(f"AI service result cached: {func.__name__}")
                except Exception as e:
                    logger.error(f"AI service cache storage error: {e}")
            
            return result
        return wrapper
    return decorator


class DatabaseConnectionOptimizer:
    """
    Database connection optimization utilities.
    """
    
    @staticmethod
    def optimize_connection_settings():
        """
        Apply database connection optimizations.
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Optimize PostgreSQL settings for better performance
            optimizations = [
                "SET work_mem = '256MB'",
                "SET maintenance_work_mem = '512MB'",
                "SET effective_cache_size = '2GB'",
                "SET random_page_cost = 1.1",
                "SET seq_page_cost = 1.0",
            ]
            
            for optimization in optimizations:
                try:
                    cursor.execute(optimization)
                    logger.debug(f"Applied DB optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Failed to apply DB optimization {optimization}: {e}")
    
    @staticmethod
    def analyze_slow_queries():
        """
        Analyze and log slow queries for optimization.
        """
        if not settings.DEBUG:
            return
        
        slow_queries = [
            query for query in connection.queries 
            if float(query['time']) > 0.1  # Queries taking more than 100ms
        ]
        
        if slow_queries:
            logger.warning(f"Found {len(slow_queries)} slow queries:")
            for query in slow_queries[:5]:  # Log first 5 slow queries
                logger.warning(f"Slow query ({query['time']}s): {query['sql'][:200]}...")


# Performance monitoring decorators
def track_performance(operation_name: str):
    """
    Decorator to track performance of operations.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceProfiler(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def batch_database_operations(batch_size: int = 100):
    """
    Decorator to batch database operations for better performance.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(items, *args, **kwargs):
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_result = func(batch, *args, **kwargs)
                results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
            return results
        return wrapper
    return decorator