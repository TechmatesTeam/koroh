#!/usr/bin/env python3
"""
Monitoring System Integration Test Script

This script tests the complete monitoring and alerting pipeline:
1. Metrics collection from all services
2. Prometheus scraping and storage
3. Grafana dashboard functionality
4. Alert rule evaluation
5. Notification system (if configured)

Usage:
    python scripts/test_monitoring_integration.py [--verbose] [--timeout=60]
"""

import argparse
import json
import time
import yaml
import requests
import subprocess
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin


class MonitoringTestSuite:
    """Comprehensive monitoring system test suite."""
    
    def __init__(self, verbose: bool = False, timeout: int = 60):
        self.verbose = verbose
        self.timeout = timeout
        self.services = {
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3001',
            'api': 'http://localhost:8000',
            'web': 'http://localhost:3000'
        }
        self.test_results = []
    
    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if self.verbose or level in ['ERROR', 'WARN']:
            print(f"[{timestamp}] {level}: {message}")
    
    def wait_for_service(self, service_name: str, url: str, max_retries: int = 10) -> bool:
        """Wait for a service to become available."""
        self.log(f"Waiting for {service_name} at {url}")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    self.log(f"{service_name} is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_retries - 1:
                time.sleep(2)
        
        self.log(f"{service_name} is not available after {max_retries} attempts", 'ERROR')
        return False
    
    def test_prometheus_metrics_collection(self) -> bool:
        """Test Prometheus metrics collection from all targets."""
        self.log("Testing Prometheus metrics collection")
        
        try:
            # Check Prometheus targets
            response = requests.get(f"{self.services['prometheus']}/api/v1/targets")
            if response.status_code != 200:
                self.log("Failed to get Prometheus targets", 'ERROR')
                return False
            
            targets_data = response.json()
            active_targets = [
                target for target in targets_data['data']['activeTargets']
                if target['health'] == 'up'
            ]
            
            self.log(f"Found {len(active_targets)} active targets")
            
            # Check specific metrics exist
            test_metrics = [
                'koroh_active_users',
                'django_http_requests_total',
                'koroh_ai_requests_total',
                'koroh_celery_tasks_processed_total'
            ]
            
            for metric in test_metrics:
                response = requests.get(
                    f"{self.services['prometheus']}/api/v1/query",
                    params={'query': metric}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['data']['result']:
                        self.log(f"✓ Metric {metric} is available")
                    else:
                        self.log(f"✗ Metric {metric} has no data", 'WARN')
                else:
                    self.log(f"✗ Failed to query metric {metric}", 'ERROR')
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Error testing Prometheus metrics: {e}", 'ERROR')
            return False
    
    def test_grafana_dashboard_queries(self) -> bool:
        """Test Grafana dashboard queries."""
        self.log("Testing Grafana dashboard queries")
        
        try:
            # Load dashboard configuration
            with open('monitoring/grafana/dashboards/koroh-platform.json', 'r') as f:
                dashboard_config = json.load(f)
            
            dashboard = dashboard_config['dashboard']
            queries_tested = 0
            queries_passed = 0
            
            # Extract and test queries from panels
            for panel in dashboard['panels']:
                if 'targets' in panel:
                    for target in panel['targets']:
                        if 'expr' in target:
                            query = target['expr']
                            queries_tested += 1
                            
                            # Test query against Prometheus
                            response = requests.get(
                                f"{self.services['prometheus']}/api/v1/query",
                                params={'query': query}
                            )
                            
                            if response.status_code == 200:
                                queries_passed += 1
                                self.log(f"✓ Query passed: {query[:50]}...")
                            else:
                                self.log(f"✗ Query failed: {query[:50]}...", 'WARN')
            
            success_rate = queries_passed / queries_tested if queries_tested > 0 else 0
            self.log(f"Dashboard queries: {queries_passed}/{queries_tested} passed ({success_rate:.1%})")
            
            return success_rate >= 0.8  # 80% success rate threshold
            
        except Exception as e:
            self.log(f"Error testing Grafana queries: {e}", 'ERROR')
            return False
    
    def test_alerting_rules(self) -> bool:
        """Test Prometheus alerting rules."""
        self.log("Testing Prometheus alerting rules")
        
        try:
            # Check rules are loaded
            response = requests.get(f"{self.services['prometheus']}/api/v1/rules")
            if response.status_code != 200:
                self.log("Failed to get Prometheus rules", 'ERROR')
                return False
            
            rules_data = response.json()
            rule_groups = rules_data['data']['groups']
            
            total_rules = sum(len(group['rules']) for group in rule_groups)
            self.log(f"Found {total_rules} alerting rules in {len(rule_groups)} groups")
            
            # Check rule syntax and evaluation
            rules_ok = 0
            for group in rule_groups:
                for rule in group['rules']:
                    if rule['type'] == 'alerting':
                        # Check rule has required fields
                        if all(key in rule for key in ['name', 'query', 'labels']):
                            rules_ok += 1
                        else:
                            self.log(f"✗ Rule {rule.get('name', 'unknown')} missing required fields", 'WARN')
            
            self.log(f"Alerting rules: {rules_ok}/{total_rules} are properly configured")
            return rules_ok == total_rules
            
        except Exception as e:
            self.log(f"Error testing alerting rules: {e}", 'ERROR')
            return False
    
    def test_alert_evaluation(self) -> bool:
        """Test alert evaluation by checking current alerts."""
        self.log("Testing alert evaluation")
        
        try:
            # Get current alerts
            response = requests.get(f"{self.services['prometheus']}/api/v1/alerts")
            if response.status_code != 200:
                self.log("Failed to get current alerts", 'ERROR')
                return False
            
            alerts_data = response.json()
            alerts = alerts_data['data']['alerts']
            
            # Count alerts by state
            alert_states = {}
            for alert in alerts:
                state = alert['state']
                alert_states[state] = alert_states.get(state, 0) + 1
            
            self.log(f"Current alerts: {alert_states}")
            
            # Check for critical alerts that shouldn't be firing in healthy system
            critical_alerts = [
                alert for alert in alerts
                if alert['labels'].get('severity') == 'critical' and alert['state'] == 'firing'
            ]
            
            if critical_alerts:
                self.log(f"⚠️  {len(critical_alerts)} critical alerts are firing", 'WARN')
                for alert in critical_alerts:
                    self.log(f"   - {alert['labels']['alertname']}: {alert['annotations'].get('summary', 'No summary')}")
            else:
                self.log("✓ No critical alerts firing")
            
            return True
            
        except Exception as e:
            self.log(f"Error testing alert evaluation: {e}", 'ERROR')
            return False
    
    def test_metrics_endpoints(self) -> bool:
        """Test metrics endpoints on all services."""
        self.log("Testing metrics endpoints")
        
        endpoints = [
            ('Django API', f"{self.services['api']}/metrics"),
            ('Next.js Web', f"{self.services['web']}/api/metrics"),
        ]
        
        all_passed = True
        
        for service_name, endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    metrics_text = response.text
                    
                    # Check Prometheus format
                    if '# HELP' in metrics_text and '# TYPE' in metrics_text:
                        self.log(f"✓ {service_name} metrics endpoint working")
                    else:
                        self.log(f"✗ {service_name} metrics not in Prometheus format", 'WARN')
                        all_passed = False
                else:
                    self.log(f"✗ {service_name} metrics endpoint returned {response.status_code}", 'ERROR')
                    all_passed = False
                    
            except Exception as e:
                self.log(f"✗ {service_name} metrics endpoint error: {e}", 'ERROR')
                all_passed = False
        
        return all_passed
    
    def test_service_discovery(self) -> bool:
        """Test Prometheus service discovery."""
        self.log("Testing Prometheus service discovery")
        
        try:
            response = requests.get(f"{self.services['prometheus']}/api/v1/targets")
            if response.status_code != 200:
                return False
            
            targets_data = response.json()
            targets = targets_data['data']['activeTargets']
            
            expected_jobs = [
                'prometheus',
                'django-api',
                'nextjs-web',
                'node-exporter'
            ]
            
            discovered_jobs = set(target['labels']['job'] for target in targets)
            
            for job in expected_jobs:
                if job in discovered_jobs:
                    self.log(f"✓ Service discovery found job: {job}")
                else:
                    self.log(f"✗ Service discovery missing job: {job}", 'WARN')
            
            return len(discovered_jobs.intersection(expected_jobs)) >= len(expected_jobs) * 0.75
            
        except Exception as e:
            self.log(f"Error testing service discovery: {e}", 'ERROR')
            return False
    
    def test_data_retention(self) -> bool:
        """Test metrics data retention."""
        self.log("Testing metrics data retention")
        
        try:
            # Query for data from 1 hour ago
            end_time = int(time.time())
            start_time = end_time - 3600  # 1 hour ago
            
            response = requests.get(
                f"{self.services['prometheus']}/api/v1/query_range",
                params={
                    'query': 'up',
                    'start': start_time,
                    'end': end_time,
                    'step': '60s'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    data_points = len(data['data']['result'][0]['values'])
                    self.log(f"✓ Found {data_points} data points over 1 hour")
                    return data_points > 0
                else:
                    self.log("✗ No historical data found", 'WARN')
                    return False
            else:
                self.log("✗ Failed to query historical data", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Error testing data retention: {e}", 'ERROR')
            return False
    
    def generate_test_metrics(self) -> bool:
        """Generate test metrics to verify collection."""
        self.log("Generating test metrics")
        
        try:
            # Generate some API requests to create metrics
            test_endpoints = [
                f"{self.services['api']}/api/v1/auth/login/",
                f"{self.services['web']}/api/metrics",
            ]
            
            for endpoint in test_endpoints:
                try:
                    # Make requests to generate metrics (expect some to fail)
                    requests.get(endpoint, timeout=5)
                except:
                    pass  # Expected for some endpoints
            
            # Wait for metrics to be scraped
            time.sleep(15)
            
            self.log("✓ Test metrics generated")
            return True
            
        except Exception as e:
            self.log(f"Error generating test metrics: {e}", 'ERROR')
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all monitoring tests."""
        self.log("Starting monitoring system integration tests")
        
        tests = [
            ('Service Availability', self.wait_for_services),
            ('Generate Test Metrics', self.generate_test_metrics),
            ('Prometheus Metrics Collection', self.test_prometheus_metrics_collection),
            ('Metrics Endpoints', self.test_metrics_endpoints),
            ('Service Discovery', self.test_service_discovery),
            ('Grafana Dashboard Queries', self.test_grafana_dashboard_queries),
            ('Alerting Rules', self.test_alerting_rules),
            ('Alert Evaluation', self.test_alert_evaluation),
            ('Data Retention', self.test_data_retention),
        ]
        
        results = {}
        passed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- Running: {test_name} ---")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.log(f"✓ {test_name}: PASSED")
                else:
                    self.log(f"✗ {test_name}: FAILED", 'ERROR')
            except Exception as e:
                results[test_name] = False
                self.log(f"✗ {test_name}: ERROR - {e}", 'ERROR')
        
        # Summary
        total = len(tests)
        success_rate = passed / total
        
        self.log(f"\n=== TEST SUMMARY ===")
        self.log(f"Tests passed: {passed}/{total} ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            self.log("✓ Monitoring system is functioning well")
        elif success_rate >= 0.6:
            self.log("⚠️  Monitoring system has some issues", 'WARN')
        else:
            self.log("✗ Monitoring system has significant problems", 'ERROR')
        
        return results
    
    def wait_for_services(self) -> bool:
        """Wait for all required services to be available."""
        all_ready = True
        
        # Check core services
        for service_name, url in self.services.items():
            if not self.wait_for_service(service_name, url):
                all_ready = False
        
        return all_ready


def main():
    """Main function to run monitoring tests."""
    parser = argparse.ArgumentParser(description='Test Koroh monitoring system')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--timeout', '-t', type=int, default=60,
                       help='Timeout for tests in seconds')
    
    args = parser.parse_args()
    
    # Run tests
    test_suite = MonitoringTestSuite(verbose=args.verbose, timeout=args.timeout)
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")
        exit(1)
    else:
        print("\n✓ All monitoring tests passed!")
        exit(0)


if __name__ == '__main__':
    main()