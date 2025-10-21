"""
Django management command to check Celery status and health.

This command provides comprehensive information about Celery workers,
queues, tasks, and overall system health.
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from koroh_platform.utils.celery_monitoring import (
    celery_monitor,
    get_celery_health_status
)


class Command(BaseCommand):
    """
    Management command to check Celery status and health.
    
    Usage:
        python manage.py celery_status
        python manage.py celery_status --workers
        python manage.py celery_status --queues
        python manage.py celery_status --tasks
        python manage.py celery_status --health
        python manage.py celery_status --json
    """
    
    help = 'Check Celery workers, queues, and task status'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--workers',
            action='store_true',
            help='Show detailed worker information'
        )
        parser.add_argument(
            '--queues',
            action='store_true',
            help='Show queue statistics'
        )
        parser.add_argument(
            '--tasks',
            action='store_true',
            help='Show task statistics'
        )
        parser.add_argument(
            '--health',
            action='store_true',
            help='Show health status only'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        parser.add_argument(
            '--task-name',
            type=str,
            help='Get statistics for specific task name'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        try:
            # Determine what information to show
            show_all = not any([
                options['workers'],
                options['queues'],
                options['tasks'],
                options['health']
            ])
            
            result = {}
            
            # Get health status
            if options['health'] or show_all:
                result['health'] = get_celery_health_status()
            
            # Get worker information
            if options['workers'] or show_all:
                result['workers'] = celery_monitor.get_worker_stats()
            
            # Get queue information
            if options['queues'] or show_all:
                result['queues'] = celery_monitor.get_queue_stats()
            
            # Get task information
            if options['tasks'] or show_all:
                task_name = options.get('task_name')
                result['tasks'] = celery_monitor.get_task_stats(task_name)
            
            # Output results
            if options['json']:
                self.stdout.write(json.dumps(result, indent=2))
            else:
                self._format_output(result, options)
                
        except Exception as e:
            raise CommandError(f'Failed to get Celery status: {e}')
    
    def _format_output(self, result, options):
        """Format and display the output in human-readable format."""
        self.stdout.write(
            self.style.SUCCESS(f"\n=== Celery Status Report ===")
        )
        self.stdout.write(f"Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        # Health status
        if 'health' in result:
            self._display_health_status(result['health'])
        
        # Worker information
        if 'workers' in result:
            self._display_worker_info(result['workers'])
        
        # Queue information
        if 'queues' in result:
            self._display_queue_info(result['queues'])
        
        # Task information
        if 'tasks' in result:
            self._display_task_info(result['tasks'])
    
    def _display_health_status(self, health_data):
        """Display health status information."""
        self.stdout.write(self.style.SUCCESS("\n--- Health Status ---"))
        
        status = health_data.get('status', 'unknown')
        if status == 'healthy':
            status_style = self.style.SUCCESS
        elif status in ['degraded', 'no_workers']:
            status_style = self.style.WARNING
        else:
            status_style = self.style.ERROR
        
        self.stdout.write(f"Overall Status: {status_style(status.upper())}")
        
        workers = health_data.get('workers', {})
        self.stdout.write(f"Total Workers: {workers.get('total_workers', 0)}")
        self.stdout.write(f"Healthy Workers: {workers.get('healthy_count', 0)}")
        
        if workers.get('unhealthy_workers'):
            self.stdout.write(
                self.style.ERROR(f"Unhealthy Workers: {len(workers['unhealthy_workers'])}")
            )
            for worker_info in workers['unhealthy_workers']:
                self.stdout.write(f"  - {worker_info['worker']}: {worker_info['response']}")
    
    def _display_worker_info(self, worker_data):
        """Display worker information."""
        self.stdout.write(self.style.SUCCESS("\n--- Worker Information ---"))
        
        if 'error' in worker_data:
            self.stdout.write(self.style.ERROR(f"Error: {worker_data['error']}"))
            return
        
        self.stdout.write(f"Total Workers: {worker_data.get('total_workers', 0)}")
        self.stdout.write(f"Total Registered Tasks: {worker_data.get('total_registered_tasks', 0)}")
        
        worker_details = worker_data.get('worker_details', {})
        if worker_details:
            self.stdout.write("\nWorker Details:")
            for worker_name, details in worker_details.items():
                self.stdout.write(f"  {worker_name}:")
                self.stdout.write(f"    Active Tasks: {details.get('active_tasks', 0)}")
                self.stdout.write(f"    Registered Tasks: {details.get('registered_tasks', 0)}")
                
                stats = details.get('stats', {})
                if stats:
                    self.stdout.write(f"    Pool: {stats.get('pool', {}).get('max-concurrency', 'N/A')}")
                    self.stdout.write(f"    Processes: {stats.get('pool', {}).get('processes', 'N/A')}")
    
    def _display_queue_info(self, queue_data):
        """Display queue information."""
        self.stdout.write(self.style.SUCCESS("\n--- Queue Information ---"))
        
        if 'error' in queue_data:
            self.stdout.write(self.style.ERROR(f"Error: {queue_data['error']}"))
            return
        
        self.stdout.write(f"Total Reserved: {queue_data.get('total_reserved', 0)}")
        self.stdout.write(f"Total Scheduled: {queue_data.get('total_scheduled', 0)}")
        self.stdout.write(f"Total Active: {queue_data.get('total_active', 0)}")
        
        queues = queue_data.get('queues', {})
        if queues:
            self.stdout.write("\nQueue Details:")
            for queue_name, stats in queues.items():
                self.stdout.write(f"  {queue_name}:")
                self.stdout.write(f"    Reserved: {stats.get('reserved', 0)}")
                self.stdout.write(f"    Scheduled: {stats.get('scheduled', 0)}")
                self.stdout.write(f"    Active: {stats.get('active', 0)}")
        else:
            self.stdout.write("No queue activity detected.")
    
    def _display_task_info(self, task_data):
        """Display task information."""
        self.stdout.write(self.style.SUCCESS("\n--- Task Information ---"))
        
        if 'error' in task_data:
            self.stdout.write(self.style.ERROR(f"Error: {task_data['error']}"))
            return
        
        task_name = task_data.get('task_name', 'all')
        self.stdout.write(f"Task: {task_name}")
        self.stdout.write(f"Total Executed: {task_data.get('total_executed', 0)}")
        self.stdout.write(f"Successful: {task_data.get('successful', 0)}")
        self.stdout.write(f"Failed: {task_data.get('failed', 0)}")
        self.stdout.write(f"Retried: {task_data.get('retried', 0)}")
        self.stdout.write(f"Average Runtime: {task_data.get('average_runtime', 0):.2f}s")
        
        if 'note' in task_data:
            self.stdout.write(f"\nNote: {task_data['note']}")