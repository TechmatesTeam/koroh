"""
Celery monitoring and management utilities.

This module provides utilities for monitoring Celery tasks, workers,
and queues, as well as handling task failures and retries.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from celery import current_app
from celery.events.state import State
from celery.events import EventReceiver
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class CeleryMonitor:
    """
    Monitor for Celery tasks and workers.
    
    Provides methods to check task status, worker health,
    and queue statistics.
    """
    
    def __init__(self):
        """Initialize the Celery monitor."""
        self.app = current_app
        self.state = State()
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active Celery workers.
        
        Returns:
            Dictionary containing worker statistics
        """
        try:
            inspect = self.app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            worker_stats = inspect.stats()
            
            stats = {
                'total_workers': len(active_workers) if active_workers else 0,
                'active_workers': list(active_workers.keys()) if active_workers else [],
                'worker_details': {},
                'total_registered_tasks': 0,
                'timestamp': timezone.now().isoformat()
            }
            
            if active_workers:
                for worker_name, tasks in active_workers.items():
                    worker_detail = {
                        'active_tasks': len(tasks),
                        'registered_tasks': len(registered_tasks.get(worker_name, [])) if registered_tasks else 0,
                        'stats': worker_stats.get(worker_name, {}) if worker_stats else {}
                    }
                    stats['worker_details'][worker_name] = worker_detail
                    stats['total_registered_tasks'] += worker_detail['registered_tasks']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {
                'error': str(e),
                'total_workers': 0,
                'timestamp': timezone.now().isoformat()
            }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Celery queues.
        
        Returns:
            Dictionary containing queue statistics
        """
        try:
            inspect = self.app.control.inspect()
            
            # Get reserved tasks (tasks currently being processed)
            reserved_tasks = inspect.reserved()
            
            # Get scheduled tasks
            scheduled_tasks = inspect.scheduled()
            
            # Get active tasks
            active_tasks = inspect.active()
            
            stats = {
                'queues': {},
                'total_reserved': 0,
                'total_scheduled': 0,
                'total_active': 0,
                'timestamp': timezone.now().isoformat()
            }
            
            # Process reserved tasks
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    stats['total_reserved'] += len(tasks)
                    for task in tasks:
                        queue_name = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue_name not in stats['queues']:
                            stats['queues'][queue_name] = {
                                'reserved': 0,
                                'scheduled': 0,
                                'active': 0
                            }
                        stats['queues'][queue_name]['reserved'] += 1
            
            # Process scheduled tasks
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    stats['total_scheduled'] += len(tasks)
                    for task in tasks:
                        queue_name = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue_name not in stats['queues']:
                            stats['queues'][queue_name] = {
                                'reserved': 0,
                                'scheduled': 0,
                                'active': 0
                            }
                        stats['queues'][queue_name]['scheduled'] += 1
            
            # Process active tasks
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    stats['total_active'] += len(tasks)
                    for task in tasks:
                        queue_name = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue_name not in stats['queues']:
                            stats['queues'][queue_name] = {
                                'reserved': 0,
                                'scheduled': 0,
                                'active': 0
                            }
                        stats['queues'][queue_name]['active'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_task_stats(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about specific tasks or all tasks.
        
        Args:
            task_name: Optional specific task name to get stats for
            
        Returns:
            Dictionary containing task statistics
        """
        try:
            # Get task statistics from cache (updated by periodic monitoring)
            cache_key = f"celery_task_stats_{task_name or 'all'}"
            cached_stats = cache.get(cache_key)
            
            if cached_stats:
                return cached_stats
            
            # If no cached stats, return basic info
            stats = {
                'task_name': task_name or 'all',
                'total_executed': 0,
                'successful': 0,
                'failed': 0,
                'retried': 0,
                'average_runtime': 0,
                'last_updated': timezone.now().isoformat(),
                'note': 'Statistics are updated periodically by monitoring tasks'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def check_worker_health(self) -> Dict[str, Any]:
        """
        Check the health of Celery workers.
        
        Returns:
            Dictionary containing worker health status
        """
        try:
            inspect = self.app.control.inspect()
            
            # Ping all workers
            ping_results = inspect.ping()
            
            health_status = {
                'healthy_workers': [],
                'unhealthy_workers': [],
                'total_workers': 0,
                'healthy_count': 0,
                'timestamp': timezone.now().isoformat()
            }
            
            if ping_results:
                for worker_name, response in ping_results.items():
                    health_status['total_workers'] += 1
                    
                    if response.get('ok') == 'pong':
                        health_status['healthy_workers'].append(worker_name)
                        health_status['healthy_count'] += 1
                    else:
                        health_status['unhealthy_workers'].append({
                            'worker': worker_name,
                            'response': response
                        })
            
            health_status['overall_health'] = (
                'healthy' if health_status['healthy_count'] == health_status['total_workers']
                else 'degraded' if health_status['healthy_count'] > 0
                else 'unhealthy'
            )
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to check worker health: {e}")
            return {
                'error': str(e),
                'overall_health': 'unknown',
                'timestamp': timezone.now().isoformat()
            }


class TaskFailureHandler:
    """
    Handler for managing task failures and retries.
    
    Provides methods to analyze task failures, implement
    custom retry logic, and send failure notifications.
    """
    
    def __init__(self):
        """Initialize the task failure handler."""
        self.logger = logging.getLogger(f"{__name__}.TaskFailureHandler")
    
    def handle_task_failure(
        self,
        task_id: str,
        task_name: str,
        error: Exception,
        traceback: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Handle a task failure with appropriate logging and notifications.
        
        Args:
            task_id: ID of the failed task
            task_name: Name of the failed task
            error: Exception that caused the failure
            traceback: Full traceback of the error
            retry_count: Number of retries attempted
            
        Returns:
            Dictionary with handling results
        """
        try:
            failure_info = {
                'task_id': task_id,
                'task_name': task_name,
                'error': str(error),
                'error_type': type(error).__name__,
                'retry_count': retry_count,
                'timestamp': timezone.now().isoformat(),
                'severity': self._determine_failure_severity(task_name, error, retry_count)
            }
            
            # Log the failure
            self.logger.error(
                f"Task failure: {task_name} (ID: {task_id}) - "
                f"Error: {error} - Retry: {retry_count}",
                extra={
                    'task_id': task_id,
                    'task_name': task_name,
                    'retry_count': retry_count,
                    'traceback': traceback
                }
            )
            
            # Store failure information in cache for monitoring
            cache_key = f"task_failure_{task_id}"
            cache.set(cache_key, failure_info, timeout=86400)  # Store for 24 hours
            
            # Update failure statistics
            self._update_failure_stats(task_name, failure_info)
            
            # Send notifications for critical failures
            if failure_info['severity'] == 'critical':
                self._send_failure_notification(failure_info, traceback)
            
            return {
                'handled': True,
                'severity': failure_info['severity'],
                'notification_sent': failure_info['severity'] == 'critical'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle task failure: {e}")
            return {'handled': False, 'error': str(e)}
    
    def _determine_failure_severity(
        self,
        task_name: str,
        error: Exception,
        retry_count: int
    ) -> str:
        """
        Determine the severity of a task failure.
        
        Args:
            task_name: Name of the failed task
            error: Exception that caused the failure
            retry_count: Number of retries attempted
            
        Returns:
            Severity level: 'low', 'medium', 'high', or 'critical'
        """
        # Critical tasks that should never fail
        critical_tasks = [
            'koroh_platform.tasks.analyze_cv_with_ai',
            'koroh_platform.tasks.generate_portfolio_with_ai',
            'authentication.tasks.send_welcome_email'
        ]
        
        # High-priority tasks
        high_priority_tasks = [
            'koroh_platform.tasks.update_job_recommendations',
            'koroh_platform.tasks.send_job_recommendations_email'
        ]
        
        # Determine base severity
        if task_name in critical_tasks:
            base_severity = 'critical'
        elif task_name in high_priority_tasks:
            base_severity = 'high'
        else:
            base_severity = 'medium'
        
        # Adjust based on error type
        if isinstance(error, (ConnectionError, TimeoutError)):
            # Network-related errors might be temporary
            if retry_count < 2:
                return 'medium'
        elif isinstance(error, (ValueError, TypeError)):
            # Data-related errors are usually critical
            return 'critical'
        
        # Adjust based on retry count
        if retry_count >= 3:
            return 'critical'  # Multiple failures indicate a serious issue
        
        return base_severity
    
    def _update_failure_stats(self, task_name: str, failure_info: Dict[str, Any]) -> None:
        """
        Update failure statistics for monitoring.
        
        Args:
            task_name: Name of the failed task
            failure_info: Information about the failure
        """
        try:
            cache_key = f"task_failure_stats_{task_name}"
            stats = cache.get(cache_key, {
                'total_failures': 0,
                'last_failure': None,
                'failure_types': {},
                'severity_counts': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            })
            
            stats['total_failures'] += 1
            stats['last_failure'] = failure_info['timestamp']
            
            error_type = failure_info['error_type']
            stats['failure_types'][error_type] = stats['failure_types'].get(error_type, 0) + 1
            
            severity = failure_info['severity']
            stats['severity_counts'][severity] += 1
            
            cache.set(cache_key, stats, timeout=86400 * 7)  # Store for 7 days
            
        except Exception as e:
            self.logger.error(f"Failed to update failure stats: {e}")
    
    def _send_failure_notification(self, failure_info: Dict[str, Any], traceback: str) -> None:
        """
        Send notification for critical task failures.
        
        Args:
            failure_info: Information about the failure
            traceback: Full traceback of the error
        """
        try:
            from django.core.mail import send_mail
            
            subject = f"Critical Task Failure: {failure_info['task_name']}"
            message = f"""
            A critical task has failed in the Koroh platform:
            
            Task: {failure_info['task_name']}
            Task ID: {failure_info['task_id']}
            Error: {failure_info['error']}
            Error Type: {failure_info['error_type']}
            Retry Count: {failure_info['retry_count']}
            Timestamp: {failure_info['timestamp']}
            
            Traceback:
            {traceback}
            
            Please investigate and resolve this issue immediately.
            """
            
            # Send to admin email if configured
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            if admin_email:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True
                )
                
                self.logger.info(f"Critical failure notification sent for task {failure_info['task_id']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send failure notification: {e}")


# Global instances for easy access
celery_monitor = CeleryMonitor()
task_failure_handler = TaskFailureHandler()


def get_celery_health_status() -> Dict[str, Any]:
    """
    Get comprehensive Celery health status.
    
    Returns:
        Dictionary containing overall Celery health information
    """
    try:
        worker_health = celery_monitor.check_worker_health()
        worker_stats = celery_monitor.get_worker_stats()
        queue_stats = celery_monitor.get_queue_stats()
        
        overall_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'workers': worker_health,
            'statistics': {
                'workers': worker_stats,
                'queues': queue_stats
            }
        }
        
        # Determine overall status
        if worker_health.get('overall_health') == 'unhealthy':
            overall_status['status'] = 'unhealthy'
        elif worker_health.get('overall_health') == 'degraded':
            overall_status['status'] = 'degraded'
        elif worker_stats.get('total_workers', 0) == 0:
            overall_status['status'] = 'no_workers'
        
        return overall_status
        
    except Exception as e:
        logger.error(f"Failed to get Celery health status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }