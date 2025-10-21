"""
Structured logging utilities for Koroh platform.

This module provides JSON formatters and logging utilities for
comprehensive log aggregation and analysis.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Formats log records as JSON objects with consistent structure
    for easy parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            ]:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class StructuredLogger:
    """
    Structured logger wrapper for consistent logging across the platform.
    """
    
    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.correlation_id = None
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking."""
        self.correlation_id = correlation_id
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data."""
        extra = kwargs.copy()
        
        if self.correlation_id:
            extra['correlation_id'] = self.correlation_id
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)


class SecurityLogger:
    """
    Security-focused logger for audit trails and security events.
    """
    
    def __init__(self):
        """Initialize security logger."""
        self.logger = logging.getLogger('koroh_platform.security')
    
    def log_authentication_attempt(
        self, 
        username: str, 
        success: bool, 
        ip_address: str,
        user_agent: str = None,
        **kwargs
    ):
        """Log authentication attempt."""
        self.logger.info(
            f"Authentication {'successful' if success else 'failed'} for user {username}",
            extra={
                'event_type': 'authentication',
                'username': username,
                'success': success,
                'ip_address': ip_address,
                'user_agent': user_agent,
                **kwargs
            }
        )
    
    def log_authorization_failure(
        self, 
        user_id: int, 
        resource: str, 
        action: str,
        ip_address: str = None,
        **kwargs
    ):
        """Log authorization failure."""
        self.logger.warning(
            f"Authorization failed for user {user_id} accessing {resource} with action {action}",
            extra={
                'event_type': 'authorization_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'ip_address': ip_address,
                **kwargs
            }
        )
    
    def log_data_access(
        self, 
        user_id: int, 
        resource_type: str, 
        resource_id: str,
        action: str,
        **kwargs
    ):
        """Log data access for audit trail."""
        self.logger.info(
            f"User {user_id} performed {action} on {resource_type} {resource_id}",
            extra={
                'event_type': 'data_access',
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                **kwargs
            }
        )
    
    def log_suspicious_activity(
        self, 
        description: str, 
        ip_address: str,
        user_id: int = None,
        **kwargs
    ):
        """Log suspicious activity."""
        self.logger.warning(
            f"Suspicious activity detected: {description}",
            extra={
                'event_type': 'suspicious_activity',
                'description': description,
                'ip_address': ip_address,
                'user_id': user_id,
                **kwargs
            }
        )


class PerformanceLogger:
    """
    Performance-focused logger for monitoring application performance.
    """
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger('koroh_platform.performance')
    
    def log_request_performance(
        self, 
        method: str, 
        path: str, 
        duration: float,
        status_code: int,
        user_id: int = None,
        **kwargs
    ):
        """Log request performance metrics."""
        self.logger.info(
            f"{method} {path} completed in {duration:.3f}s with status {status_code}",
            extra={
                'event_type': 'request_performance',
                'method': method,
                'path': path,
                'duration': duration,
                'status_code': status_code,
                'user_id': user_id,
                **kwargs
            }
        )
    
    def log_database_query_performance(
        self, 
        query_type: str, 
        duration: float,
        table: str = None,
        **kwargs
    ):
        """Log database query performance."""
        self.logger.info(
            f"Database {query_type} query completed in {duration:.3f}s",
            extra={
                'event_type': 'database_performance',
                'query_type': query_type,
                'duration': duration,
                'table': table,
                **kwargs
            }
        )
    
    def log_ai_service_performance(
        self, 
        service_type: str, 
        model: str, 
        duration: float,
        token_usage: Dict[str, int] = None,
        **kwargs
    ):
        """Log AI service performance."""
        self.logger.info(
            f"AI service {service_type} with model {model} completed in {duration:.3f}s",
            extra={
                'event_type': 'ai_service_performance',
                'service_type': service_type,
                'model': model,
                'duration': duration,
                'token_usage': token_usage,
                **kwargs
            }
        )


class AIServicesLogger:
    """
    Specialized logger for AI services and AWS Bedrock interactions.
    """
    
    def __init__(self):
        """Initialize AI services logger."""
        self.logger = logging.getLogger('koroh_platform.ai_services')
    
    def log_ai_request(
        self, 
        service_type: str, 
        model: str, 
        input_size: int,
        success: bool,
        duration: float = None,
        error_message: str = None,
        **kwargs
    ):
        """Log AI service request."""
        status = 'success' if success else 'error'
        message = f"AI {service_type} request with model {model} {status}"
        
        if error_message:
            message += f": {error_message}"
        
        log_level = logging.INFO if success else logging.ERROR
        
        self.logger.log(
            log_level,
            message,
            extra={
                'event_type': 'ai_request',
                'service_type': service_type,
                'model': model,
                'input_size': input_size,
                'success': success,
                'duration': duration,
                'error_message': error_message,
                **kwargs
            }
        )
    
    def log_token_usage(
        self, 
        service_type: str, 
        model: str, 
        input_tokens: int,
        output_tokens: int,
        **kwargs
    ):
        """Log token usage for cost tracking."""
        self.logger.info(
            f"Token usage for {service_type} with {model}: {input_tokens} input, {output_tokens} output",
            extra={
                'event_type': 'token_usage',
                'service_type': service_type,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                **kwargs
            }
        )


class CeleryLogger:
    """
    Specialized logger for Celery task monitoring.
    """
    
    def __init__(self):
        """Initialize Celery logger."""
        self.logger = logging.getLogger('koroh_platform.celery')
    
    def log_task_start(self, task_name: str, task_id: str, **kwargs):
        """Log task start."""
        self.logger.info(
            f"Celery task {task_name} started",
            extra={
                'event_type': 'task_start',
                'task_name': task_name,
                'task_id': task_id,
                **kwargs
            }
        )
    
    def log_task_completion(
        self, 
        task_name: str, 
        task_id: str, 
        duration: float,
        success: bool,
        error_message: str = None,
        **kwargs
    ):
        """Log task completion."""
        status = 'completed' if success else 'failed'
        message = f"Celery task {task_name} {status} in {duration:.3f}s"
        
        if error_message:
            message += f": {error_message}"
        
        log_level = logging.INFO if success else logging.ERROR
        
        self.logger.log(
            log_level,
            message,
            extra={
                'event_type': 'task_completion',
                'task_name': task_name,
                'task_id': task_id,
                'duration': duration,
                'success': success,
                'error_message': error_message,
                **kwargs
            }
        )


# Global logger instances
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()
ai_services_logger = AIServicesLogger()
celery_logger = CeleryLogger()


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


class LoggingMiddleware:
    """
    Django middleware for request logging and correlation ID tracking.
    """
    
    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request and response."""
        # Generate correlation ID
        correlation_id = generate_correlation_id()
        request.correlation_id = correlation_id
        
        # Start timing
        start_time = datetime.utcnow()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Log request performance
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        performance_logger.log_request_performance(
            method=request.method,
            path=request.path,
            duration=duration,
            status_code=response.status_code,
            user_id=user_id,
            correlation_id=correlation_id,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Add correlation ID to response headers
        response['X-Correlation-ID'] = correlation_id
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip