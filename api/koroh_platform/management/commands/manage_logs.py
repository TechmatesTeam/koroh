"""
Django management command for log management and analysis.

This command provides utilities for log rotation, analysis, and maintenance.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage application logs - rotate, analyze, and maintain log files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['rotate', 'analyze', 'clean', 'stats'],
            default='stats',
            help='Action to perform on logs'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for log retention (default: 30)'
        )
        parser.add_argument(
            '--size-limit',
            type=int,
            default=50,
            help='Size limit in MB for log rotation (default: 50)'
        )
        parser.add_argument(
            '--log-type',
            type=str,
            choices=['all', 'django', 'errors', 'security', 'ai_services', 'celery', 'performance'],
            default='all',
            help='Type of logs to process'
        )

    def handle(self, *args, **options):
        """Handle the log management command."""
        
        action = options['action']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting log management action: {action}')
        )
        
        try:
            if action == 'rotate':
                self.rotate_logs(options)
            elif action == 'analyze':
                self.analyze_logs(options)
            elif action == 'clean':
                self.clean_logs(options)
            elif action == 'stats':
                self.show_log_stats(options)
            
            self.stdout.write(
                self.style.SUCCESS(f'Log management action {action} completed successfully')
            )
            
        except Exception as e:
            logger.error(f"Log management failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Log management action {action} failed: {e}')
            )
            raise

    def get_log_files(self, log_type='all'):
        """Get list of log files based on type."""
        
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        
        if not logs_dir.exists():
            return []
        
        if log_type == 'all':
            return list(logs_dir.glob('*.log'))
        else:
            return list(logs_dir.glob(f'{log_type}.log'))

    def rotate_logs(self, options):
        """Rotate log files based on size."""
        
        size_limit = options['size_limit'] * 1024 * 1024  # Convert MB to bytes
        log_type = options['log_type']
        
        log_files = self.get_log_files(log_type)
        
        for log_file in log_files:
            if log_file.stat().st_size > size_limit:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                rotated_name = f"{log_file.stem}_{timestamp}.log"
                rotated_path = log_file.parent / rotated_name
                
                # Move current log to rotated name
                log_file.rename(rotated_path)
                
                # Compress the rotated log
                with open(rotated_path, 'rb') as f_in:
                    with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # Remove uncompressed rotated file
                rotated_path.unlink()
                
                self.stdout.write(f'Rotated and compressed: {log_file.name}')

    def clean_logs(self, options):
        """Clean old log files."""
        
        retention_days = options['days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        log_type = options['log_type']
        
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        
        if not logs_dir.exists():
            return
        
        # Clean rotated and compressed logs
        pattern = '*.log.gz' if log_type == 'all' else f'{log_type}_*.log.gz'
        
        cleaned_count = 0
        for log_file in logs_dir.glob(pattern):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                log_file.unlink()
                cleaned_count += 1
                self.stdout.write(f'Removed old log: {log_file.name}')
        
        self.stdout.write(f'Cleaned {cleaned_count} old log files')

    def analyze_logs(self, options):
        """Analyze log files for patterns and statistics."""
        
        log_type = options['log_type']
        log_files = self.get_log_files(log_type)
        
        analysis_results = {
            'total_files': len(log_files),
            'total_size_mb': 0,
            'log_levels': {},
            'error_patterns': {},
            'ai_service_stats': {},
            'performance_stats': {},
            'security_events': 0
        }
        
        for log_file in log_files:
            file_size_mb = log_file.stat().st_size / (1024 * 1024)
            analysis_results['total_size_mb'] += file_size_mb
            
            self.stdout.write(f'Analyzing: {log_file.name} ({file_size_mb:.2f} MB)')
            
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            if log_file.name.endswith('.log') and line.strip().startswith('{'):
                                # JSON formatted log
                                log_entry = json.loads(line.strip())
                                self._analyze_json_log_entry(log_entry, analysis_results)
                            else:
                                # Plain text log
                                self._analyze_text_log_entry(line, analysis_results)
                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue
                        except Exception as e:
                            # Skip problematic lines
                            continue
            
            except Exception as e:
                self.stdout.write(f'Error reading {log_file.name}: {e}')
        
        self._display_analysis_results(analysis_results)

    def _analyze_json_log_entry(self, log_entry, results):
        """Analyze a JSON log entry."""
        
        # Count log levels
        level = log_entry.get('level', 'UNKNOWN')
        results['log_levels'][level] = results['log_levels'].get(level, 0) + 1
        
        # Analyze AI service logs
        if log_entry.get('logger', '').endswith('ai_services'):
            service_type = log_entry.get('extra', {}).get('service_type')
            if service_type:
                if service_type not in results['ai_service_stats']:
                    results['ai_service_stats'][service_type] = {
                        'requests': 0,
                        'errors': 0,
                        'total_duration': 0
                    }
                
                results['ai_service_stats'][service_type]['requests'] += 1
                
                if level == 'ERROR':
                    results['ai_service_stats'][service_type]['errors'] += 1
                
                duration = log_entry.get('extra', {}).get('duration')
                if duration:
                    results['ai_service_stats'][service_type]['total_duration'] += float(duration)
        
        # Analyze performance logs
        if log_entry.get('logger', '').endswith('performance'):
            event_type = log_entry.get('extra', {}).get('event_type')
            if event_type not in results['performance_stats']:
                results['performance_stats'][event_type] = {
                    'count': 0,
                    'total_duration': 0
                }
            
            results['performance_stats'][event_type]['count'] += 1
            
            duration = log_entry.get('extra', {}).get('duration')
            if duration:
                results['performance_stats'][event_type]['total_duration'] += float(duration)
        
        # Count security events
        if log_entry.get('logger', '').endswith('security'):
            results['security_events'] += 1
        
        # Analyze error patterns
        if level in ['ERROR', 'CRITICAL']:
            error_msg = log_entry.get('message', '')
            if error_msg:
                # Extract error type from message
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg[:50]
                results['error_patterns'][error_type] = results['error_patterns'].get(error_type, 0) + 1

    def _analyze_text_log_entry(self, line, results):
        """Analyze a plain text log entry."""
        
        # Simple level detection for plain text logs
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            if level in line:
                results['log_levels'][level] = results['log_levels'].get(level, 0) + 1
                break
        
        # Count security events
        if 'SECURITY' in line:
            results['security_events'] += 1

    def _display_analysis_results(self, results):
        """Display log analysis results."""
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('LOG ANALYSIS RESULTS'))
        self.stdout.write('='*50)
        
        self.stdout.write(f"Total log files: {results['total_files']}")
        self.stdout.write(f"Total size: {results['total_size_mb']:.2f} MB")
        
        # Log levels
        self.stdout.write('\nLog Levels:')
        for level, count in sorted(results['log_levels'].items()):
            self.stdout.write(f"  {level}: {count}")
        
        # Error patterns
        if results['error_patterns']:
            self.stdout.write('\nTop Error Patterns:')
            sorted_errors = sorted(results['error_patterns'].items(), key=lambda x: x[1], reverse=True)
            for error, count in sorted_errors[:10]:
                self.stdout.write(f"  {error}: {count}")
        
        # AI service statistics
        if results['ai_service_stats']:
            self.stdout.write('\nAI Service Statistics:')
            for service, stats in results['ai_service_stats'].items():
                avg_duration = stats['total_duration'] / stats['requests'] if stats['requests'] > 0 else 0
                error_rate = (stats['errors'] / stats['requests'] * 100) if stats['requests'] > 0 else 0
                self.stdout.write(f"  {service}:")
                self.stdout.write(f"    Requests: {stats['requests']}")
                self.stdout.write(f"    Errors: {stats['errors']} ({error_rate:.1f}%)")
                self.stdout.write(f"    Avg Duration: {avg_duration:.3f}s")
        
        # Performance statistics
        if results['performance_stats']:
            self.stdout.write('\nPerformance Statistics:')
            for event_type, stats in results['performance_stats'].items():
                avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
                self.stdout.write(f"  {event_type}:")
                self.stdout.write(f"    Count: {stats['count']}")
                self.stdout.write(f"    Avg Duration: {avg_duration:.3f}s")
        
        # Security events
        self.stdout.write(f"\nSecurity Events: {results['security_events']}")

    def show_log_stats(self, options):
        """Show basic log file statistics."""
        
        log_type = options['log_type']
        log_files = self.get_log_files(log_type)
        
        if not log_files:
            self.stdout.write('No log files found')
            return
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('LOG FILE STATISTICS'))
        self.stdout.write('='*50)
        
        total_size = 0
        for log_file in log_files:
            size_mb = log_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            self.stdout.write(
                f"{log_file.name}: {size_mb:.2f} MB (modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})"
            )
        
        self.stdout.write(f"\nTotal size: {total_size:.2f} MB")
        self.stdout.write(f"Total files: {len(log_files)}")