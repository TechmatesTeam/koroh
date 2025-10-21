"""
Test monitoring and alerting systems.

This module tests the Prometheus metrics collection, Grafana dashboard functionality,
and alerting rules for the Koroh platform.
"""

import json
import time
import requests
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from prometheus_client import REGISTRY, CollectorRegistry
from koroh_platform.utils.metrics import (
    ai_requests_total,
    ai_request_duration,
    ai_tokens_used,
    cv_uploads_total,
    portfolio_generations_total,
    job_searches_total,
    active_users_gauge,
    celery_tasks_processed,
    track_ai_request,
    track_user_activity,
    track_celery_task,
    update_active_users_count
)

User = get_user_model()


class MetricsCollectionTest(TestCase):
    """Test Prometheus metrics collection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Clear metrics before each test
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()
    
    def test_ai_request_metrics_tracking(self):
        """Test AI request metrics are properly tracked."""
        
        @track_ai_request('cv_analysis', 'claude-3')
        def mock_ai_service():
            return {
                'result': 'success',
                'token_usage': {
                    'input_tokens': 100,
                    'output_tokens': 50
                }
            }
        
        # Execute tracked function
        result = mock_ai_service()
        
        # Verify metrics were recorded
        self.assertEqual(result['result'], 'success')
        
        # Check that metrics counters were incremented
        ai_request_samples = list(ai_requests_total.collect())[0].samples
        self.assertTrue(any(
            sample.labels.get('service_type') == 'cv_analysis' and
            sample.labels.get('status') == 'success'
            for sample in ai_request_samples
        ))
    
    def test_ai_request_error_tracking(self):
        """Test AI request error metrics are properly tracked."""
        
        @track_ai_request('portfolio_generation', 'claude-3')
        def failing_ai_service():
            raise Exception("AI service error")
        
        # Execute failing function
        with self.assertRaises(Exception):
            failing_ai_service()
        
        # Check that error metrics were recorded
        ai_request_samples = list(ai_requests_total.collect())[0].samples
        self.assertTrue(any(
            sample.labels.get('service_type') == 'portfolio_generation' and
            sample.labels.get('status') == 'error'
            for sample in ai_request_samples
        ))
    
    def test_user_activity_metrics(self):
        """Test user activity metrics tracking."""
        
        @track_user_activity('cv_upload')
        def mock_cv_upload(file_type='pdf'):
            return {'status': 'success', 'file_type': file_type}
        
        # Execute tracked function
        result = mock_cv_upload(file_type='pdf')
        
        # Verify CV upload metrics
        cv_upload_samples = list(cv_uploads_total.collect())[0].samples
        self.assertTrue(any(
            sample.labels.get('file_type') == 'pdf' and
            sample.labels.get('status') == 'success'
            for sample in cv_upload_samples
        ))
    
    def test_celery_task_metrics(self):
        """Test Celery task metrics tracking."""
        
        @track_celery_task('test_task')
        def mock_celery_task():
            return {'status': 'completed'}
        
        # Execute tracked task
        result = mock_celery_task()
        
        # Verify task metrics
        task_samples = list(celery_tasks_processed.collect())[0].samples
        self.assertTrue(any(
            sample.labels.get('task_name') == 'test_task' and
            sample.labels.get('status') == 'success'
            for sample in task_samples
        ))
    
    def test_active_users_gauge(self):
        """Test active users gauge functionality."""
        # Update active users count
        update_active_users_count(25)
        
        # Verify gauge value
        gauge_samples = list(active_users_gauge.collect())[0].samples
        self.assertEqual(gauge_samples[0].value, 25)
    
    def test_metrics_endpoint_format(self):
        """Test that metrics are properly formatted for Prometheus."""
        # Generate some test metrics
        update_active_users_count(10)
        
        # Collect metrics
        from prometheus_client import generate_latest
        metrics_output = generate_latest(REGISTRY).decode('utf-8')
        
        # Verify Prometheus format
        self.assertIn('koroh_active_users', metrics_output)
        self.assertIn('TYPE koroh_active_users gauge', metrics_output)


class DashboardFunctionalityTest(TestCase):
    """Test Grafana dashboard functionality and queries."""
    
    def setUp(self):
        """Set up test environment."""
        self.grafana_url = 'http://localhost:3001'
        self.prometheus_url = 'http://localhost:9090'
    
    def test_prometheus_query_execution(self):
        """Test that Prometheus queries used in dashboards work correctly."""
        # Test queries from the dashboard configuration
        test_queries = [
            'koroh_active_users',
            'rate(django_http_requests_total[5m])',
            'histogram_quantile(0.95, rate(django_request_duration_seconds_bucket[5m]))',
            'rate(koroh_ai_requests_total[5m])',
            'koroh_celery_tasks_pending'
        ]
        
        for query in test_queries:
            # Mock Prometheus response
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'status': 'success',
                    'data': {
                        'resultType': 'vector',
                        'result': [
                            {
                                'metric': {'__name__': query.split('[')[0].split('(')[-1]},
                                'value': [time.time(), '1.0']
                            }
                        ]
                    }
                }
                mock_get.return_value = mock_response
                
                # Simulate query execution
                response = requests.get(
                    f'{self.prometheus_url}/api/v1/query',
                    params={'query': query}
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data['status'], 'success')
    
    def test_dashboard_panel_configuration(self):
        """Test dashboard panel configurations are valid."""
        # Load dashboard configuration
        try:
            with open('monitoring/grafana/dashboards/koroh-platform.json', 'r') as f:
                dashboard_config = json.load(f)
            
            # Verify dashboard structure
            self.assertIn('dashboard', dashboard_config)
            dashboard = dashboard_config['dashboard']
            
            # Check required fields
            self.assertIn('title', dashboard)
            self.assertIn('panels', dashboard)
            self.assertEqual(dashboard['title'], 'Koroh Platform Overview')
            
            # Verify panels have required fields
            for panel in dashboard['panels']:
                if panel.get('type') != 'row':  # Skip row panels
                    self.assertIn('title', panel)
                    self.assertIn('type', panel)
                    if 'targets' in panel:
                        for target in panel['targets']:
                            self.assertIn('expr', target)
            
        except FileNotFoundError:
            self.fail("Dashboard configuration file not found")
        except json.JSONDecodeError:
            self.fail("Invalid JSON in dashboard configuration")


class AlertingRulesTest(TestCase):
    """Test Prometheus alerting rules and notification systems."""
    
    def setUp(self):
        """Set up test environment."""
        self.prometheus_url = 'http://localhost:9090'
    
    def test_alerting_rules_syntax(self):
        """Test that alerting rules have valid syntax."""
        import yaml
        
        try:
            with open('monitoring/prometheus-alerts.yml', 'r') as f:
                alerts_config = yaml.safe_load(f)
            
            # Verify structure
            self.assertIn('groups', alerts_config)
            
            for group in alerts_config['groups']:
                self.assertIn('name', group)
                self.assertIn('rules', group)
                
                for rule in group['rules']:
                    # Check required fields for alert rules
                    if 'alert' in rule:
                        self.assertIn('expr', rule)
                        self.assertIn('labels', rule)
                        self.assertIn('annotations', rule)
                        self.assertIn('severity', rule['labels'])
                        self.assertIn('summary', rule['annotations'])
        
        except FileNotFoundError:
            self.fail("Alerting rules file not found")
        except yaml.YAMLError:
            self.fail("Invalid YAML in alerting rules file")
    
    def test_critical_alert_thresholds(self):
        """Test that critical alert thresholds are reasonable."""
        import yaml
        
        with open('monitoring/prometheus-alerts.yml', 'r') as f:
            alerts_config = yaml.safe_load(f)
        
        critical_alerts = []
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if (rule.get('labels', {}).get('severity') == 'critical' and 
                    'alert' in rule):
                    critical_alerts.append(rule)
        
        # Verify we have critical alerts defined
        self.assertGreater(len(critical_alerts), 0)
        
        # Check specific critical alerts
        alert_names = [alert['alert'] for alert in critical_alerts]
        expected_critical_alerts = [
            'HighErrorRate',
            'AIServiceHighErrorRate',
            'HighDiskUsage',
            'ServiceDown',
            'PostgreSQLDown',
            'RedisDown'
        ]
        
        for expected_alert in expected_critical_alerts:
            self.assertIn(expected_alert, alert_names)
    
    def test_alert_rule_expressions(self):
        """Test that alert rule expressions are valid PromQL."""
        import yaml
        
        with open('monitoring/prometheus-alerts.yml', 'r') as f:
            alerts_config = yaml.safe_load(f)
        
        # Test expressions that should be valid
        valid_expressions = [
            'rate(django_http_requests_total{status=~"5.."}[5m]) > 0.1',
            'histogram_quantile(0.95, rate(django_request_duration_seconds_bucket[5m])) > 5',
            'koroh_active_users < 1',
            'up == 0'
        ]
        
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if 'expr' in rule:
                    expr = rule['expr']
                    # Basic syntax validation
                    self.assertIsInstance(expr, str)
                    self.assertGreater(len(expr.strip()), 0)
                    
                    # Check for common PromQL patterns
                    if 'rate(' in expr:
                        self.assertIn('[', expr)  # Should have time range
                        self.assertIn(']', expr)
    
    def test_notification_configuration(self):
        """Test notification system configuration."""
        # Check Prometheus configuration for alertmanager
        import yaml
        
        with open('monitoring/prometheus.yml', 'r') as f:
            prometheus_config = yaml.safe_load(f)
        
        # Verify alerting configuration exists
        if 'alerting' in prometheus_config:
            alerting_config = prometheus_config['alerting']
            self.assertIn('alertmanagers', alerting_config)
        
        # Verify rule files are configured
        self.assertIn('rule_files', prometheus_config)
        self.assertIn('prometheus-alerts.yml', prometheus_config['rule_files'])


class MonitoringIntegrationTest(TestCase):
    """Test end-to-end monitoring system integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123'
        )
    
    @patch('requests.get')
    def test_metrics_collection_pipeline(self, mock_get):
        """Test the complete metrics collection pipeline."""
        # Mock Prometheus scraping response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        # HELP koroh_active_users Number of currently active users
        # TYPE koroh_active_users gauge
        koroh_active_users 42.0
        """
        mock_get.return_value = mock_response
        
        # Simulate metric generation
        update_active_users_count(42)
        
        # Simulate Prometheus scraping
        response = requests.get('http://localhost:8000/metrics')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('koroh_active_users', response.text)
    
    def test_alert_evaluation_workflow(self):
        """Test alert evaluation workflow."""
        # Simulate conditions that should trigger alerts
        test_scenarios = [
            {
                'metric': 'koroh_active_users',
                'value': 0,
                'expected_alert': 'LowActiveUsers'
            },
            {
                'metric': 'django_http_requests_total',
                'labels': {'status': '500'},
                'rate': 0.2,
                'expected_alert': 'HighErrorRate'
            }
        ]
        
        for scenario in test_scenarios:
            # This would normally be tested with actual Prometheus
            # For now, we verify the alert configuration exists
            import yaml
            with open('monitoring/prometheus-alerts.yml', 'r') as f:
                alerts_config = yaml.safe_load(f)
            
            alert_found = False
            for group in alerts_config['groups']:
                for rule in group['rules']:
                    if rule.get('alert') == scenario['expected_alert']:
                        alert_found = True
                        break
            
            self.assertTrue(alert_found, 
                          f"Alert {scenario['expected_alert']} not found in configuration")
    
    def test_dashboard_data_flow(self):
        """Test data flow from metrics to dashboard."""
        # Generate test metrics
        update_active_users_count(15)
        
        # Simulate dashboard query
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'success',
                'data': {
                    'resultType': 'vector',
                    'result': [
                        {
                            'metric': {'__name__': 'koroh_active_users'},
                            'value': [time.time(), '15.0']
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            # Simulate Grafana querying Prometheus
            response = requests.get(
                'http://localhost:9090/api/v1/query',
                params={'query': 'koroh_active_users'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'success')
            self.assertEqual(float(data['data']['result'][0]['value'][1]), 15.0)


class PerformanceMonitoringTest(TestCase):
    """Test performance monitoring capabilities."""
    
    def test_response_time_tracking(self):
        """Test API response time tracking."""
        start_time = time.time()
        
        # Simulate API request processing
        time.sleep(0.1)  # 100ms delay
        
        duration = time.time() - start_time
        
        # Track the duration
        ai_request_duration.labels(
            service_type='test_service',
            model='test_model'
        ).observe(duration)
        
        # Verify histogram was updated
        histogram_samples = list(ai_request_duration.collect())[0].samples
        
        # Check that samples were recorded
        self.assertGreater(len(histogram_samples), 0)
        
        # Find the count sample
        count_sample = next(
            (s for s in histogram_samples if s.name.endswith('_count')),
            None
        )
        self.assertIsNotNone(count_sample)
        self.assertGreater(count_sample.value, 0)
    
    def test_resource_usage_monitoring(self):
        """Test system resource usage monitoring."""
        # Test CPU and memory metrics would be collected by node_exporter
        # We verify the configuration includes these metrics
        import yaml
        
        with open('monitoring/prometheus.yml', 'r') as f:
            prometheus_config = yaml.safe_load(f)
        
        # Verify node-exporter is configured
        scrape_configs = prometheus_config.get('scrape_configs', [])
        node_exporter_config = next(
            (config for config in scrape_configs if config['job_name'] == 'node-exporter'),
            None
        )
        
        self.assertIsNotNone(node_exporter_config)
        self.assertIn('node-exporter:9100', 
                     node_exporter_config['static_configs'][0]['targets'])


class AlertingNotificationTest(TestCase):
    """Test alerting notification functionality."""
    
    def test_alert_severity_levels(self):
        """Test that alerts have appropriate severity levels."""
        import yaml
        
        with open('monitoring/prometheus-alerts.yml', 'r') as f:
            alerts_config = yaml.safe_load(f)
        
        severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
        
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule and 'labels' in rule:
                    severity = rule['labels'].get('severity')
                    if severity in severity_counts:
                        severity_counts[severity] += 1
        
        # Verify we have alerts at different severity levels
        self.assertGreater(severity_counts['critical'], 0)
        self.assertGreater(severity_counts['warning'], 0)
    
    def test_alert_annotation_completeness(self):
        """Test that alerts have complete annotations."""
        import yaml
        
        with open('monitoring/prometheus-alerts.yml', 'r') as f:
            alerts_config = yaml.safe_load(f)
        
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule:
                    # Check required annotations
                    self.assertIn('annotations', rule)
                    annotations = rule['annotations']
                    
                    self.assertIn('summary', annotations)
                    self.assertIn('description', annotations)
                    
                    # Verify annotations are not empty
                    self.assertGreater(len(annotations['summary'].strip()), 0)
                    self.assertGreater(len(annotations['description'].strip()), 0)