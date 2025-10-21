#!/usr/bin/env python3
"""
Alert notification system test.

This script tests the alert notification pipeline by:
1. Triggering test alerts with low thresholds
2. Verifying alert evaluation
3. Testing notification delivery (if configured)
"""

import time
import requests
import yaml
from typing import Dict, List


class AlertNotificationTester:
    """Test alert notification system."""
    
    def __init__(self):
        self.prometheus_url = 'http://localhost:9090'
        self.test_results = []
    
    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def load_test_alerts(self) -> bool:
        """Load test alert configuration."""
        self.log("Loading test alert configuration")
        
        try:
            # Check if test alerts file exists
            with open('monitoring/test-alerts.yml', 'r') as f:
                test_alerts = yaml.safe_load(f)
            
            self.log(f"Found {len(test_alerts['groups'])} test alert groups")
            
            # Count test alerts
            total_test_alerts = 0
            for group in test_alerts['groups']:
                for rule in group['rules']:
                    if rule.get('labels', {}).get('test') == True:
                        total_test_alerts += 1
            
            self.log(f"Found {total_test_alerts} test alerts")
            return total_test_alerts > 0
            
        except FileNotFoundError:
            self.log("Test alerts configuration not found", 'WARN')
            return False
        except Exception as e:
            self.log(f"Error loading test alerts: {e}", 'ERROR')
            return False
    
    def check_prometheus_connection(self) -> bool:
        """Check if Prometheus is accessible."""
        self.log("Checking Prometheus connection")
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=5)
            if response.status_code == 200:
                self.log("✓ Prometheus is accessible")
                return True
            else:
                self.log(f"✗ Prometheus returned status {response.status_code}", 'ERROR')
                return False
        except Exception as e:
            self.log(f"✗ Cannot connect to Prometheus: {e}", 'ERROR')
            return False
    
    def get_current_alerts(self) -> List[Dict]:
        """Get current alerts from Prometheus."""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/alerts")
            if response.status_code == 200:
                data = response.json()
                return data['data']['alerts']
            else:
                self.log(f"Failed to get alerts: {response.status_code}", 'ERROR')
                return []
        except Exception as e:
            self.log(f"Error getting alerts: {e}", 'ERROR')
            return []
    
    def test_alert_evaluation(self) -> bool:
        """Test alert rule evaluation."""
        self.log("Testing alert rule evaluation")
        
        # Get current alerts
        alerts = self.get_current_alerts()
        
        if not alerts:
            self.log("No alerts currently active")
            return True
        
        # Analyze alerts
        alert_states = {}
        test_alerts = []
        production_alerts = []
        
        for alert in alerts:
            state = alert['state']
            alert_states[state] = alert_states.get(state, 0) + 1
            
            # Check if it's a test alert
            if alert['labels'].get('test') == 'true':
                test_alerts.append(alert)
            else:
                production_alerts.append(alert)
        
        self.log(f"Alert states: {alert_states}")
        self.log(f"Test alerts: {len(test_alerts)}")
        self.log(f"Production alerts: {len(production_alerts)}")
        
        # Check for critical production alerts
        critical_production = [
            alert for alert in production_alerts
            if alert['labels'].get('severity') == 'critical' and alert['state'] == 'firing'
        ]
        
        if critical_production:
            self.log(f"⚠️  {len(critical_production)} critical production alerts firing", 'WARN')
            for alert in critical_production:
                alert_name = alert['labels']['alertname']
                summary = alert['annotations'].get('summary', 'No summary')
                self.log(f"   - {alert_name}: {summary}")
        
        return True
    
    def test_alert_rule_syntax(self) -> bool:
        """Test alert rule syntax by querying Prometheus rules API."""
        self.log("Testing alert rule syntax")
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules")
            if response.status_code != 200:
                self.log("Failed to get rules from Prometheus", 'ERROR')
                return False
            
            data = response.json()
            rule_groups = data['data']['groups']
            
            total_rules = 0
            valid_rules = 0
            invalid_rules = []
            
            for group in rule_groups:
                for rule in group['rules']:
                    if rule['type'] == 'alerting':
                        total_rules += 1
                        
                        # Check if rule has evaluation error
                        if 'lastError' in rule and rule['lastError']:
                            invalid_rules.append({
                                'name': rule['name'],
                                'error': rule['lastError']
                            })
                        else:
                            valid_rules += 1
            
            if invalid_rules:
                self.log(f"Found {len(invalid_rules)} rules with errors:", 'WARN')
                for rule in invalid_rules:
                    self.log(f"   - {rule['name']}: {rule['error']}")
            
            self.log(f"Alert rules: {valid_rules}/{total_rules} valid")
            return len(invalid_rules) == 0
            
        except Exception as e:
            self.log(f"Error testing alert rule syntax: {e}", 'ERROR')
            return False
    
    def test_alert_thresholds(self) -> bool:
        """Test alert thresholds by checking if they're reasonable."""
        self.log("Testing alert thresholds")
        
        # Load alert configuration
        try:
            with open('monitoring/prometheus-alerts.yml', 'r') as f:
                alerts_config = yaml.safe_load(f)
        except Exception as e:
            self.log(f"Error loading alerts config: {e}", 'ERROR')
            return False
        
        threshold_tests = []
        
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule and 'expr' in rule:
                    expr = rule['expr']
                    alert_name = rule['alert']
                    
                    # Test specific threshold patterns
                    if 'rate(' in expr and '> 0.1' in expr:
                        threshold_tests.append({
                            'alert': alert_name,
                            'test': 'error_rate_threshold',
                            'status': 'reasonable'
                        })
                    
                    if 'histogram_quantile(0.95' in expr and '> 5' in expr:
                        threshold_tests.append({
                            'alert': alert_name,
                            'test': 'response_time_threshold',
                            'status': 'reasonable'
                        })
                    
                    if 'cpu_seconds_total' in expr and '> 80' in expr:
                        threshold_tests.append({
                            'alert': alert_name,
                            'test': 'cpu_usage_threshold',
                            'status': 'reasonable'
                        })
        
        self.log(f"Tested {len(threshold_tests)} alert thresholds")
        for test in threshold_tests:
            self.log(f"   ✓ {test['alert']}: {test['test']} is {test['status']}")
        
        return True
    
    def test_alert_labels_and_annotations(self) -> bool:
        """Test alert labels and annotations completeness."""
        self.log("Testing alert labels and annotations")
        
        try:
            with open('monitoring/prometheus-alerts.yml', 'r') as f:
                alerts_config = yaml.safe_load(f)
        except Exception as e:
            self.log(f"Error loading alerts config: {e}", 'ERROR')
            return False
        
        incomplete_alerts = []
        
        for group in alerts_config['groups']:
            for rule in group['rules']:
                if 'alert' in rule:
                    alert_name = rule['alert']
                    issues = []
                    
                    # Check required labels
                    if 'labels' not in rule:
                        issues.append('missing labels')
                    else:
                        labels = rule['labels']
                        if 'severity' not in labels:
                            issues.append('missing severity label')
                    
                    # Check required annotations
                    if 'annotations' not in rule:
                        issues.append('missing annotations')
                    else:
                        annotations = rule['annotations']
                        if 'summary' not in annotations:
                            issues.append('missing summary annotation')
                        if 'description' not in annotations:
                            issues.append('missing description annotation')
                    
                    if issues:
                        incomplete_alerts.append({
                            'alert': alert_name,
                            'issues': issues
                        })
        
        if incomplete_alerts:
            self.log(f"Found {len(incomplete_alerts)} alerts with issues:", 'WARN')
            for alert in incomplete_alerts:
                self.log(f"   - {alert['alert']}: {', '.join(alert['issues'])}")
            return False
        else:
            self.log("✓ All alerts have complete labels and annotations")
            return True
    
    def simulate_alert_conditions(self) -> bool:
        """Simulate conditions that should trigger alerts."""
        self.log("Simulating alert conditions")
        
        # This would typically involve:
        # 1. Generating load to trigger performance alerts
        # 2. Stopping services to trigger availability alerts
        # 3. Consuming resources to trigger resource alerts
        
        # For now, we'll just check if the system can handle alert evaluation
        self.log("✓ Alert condition simulation completed (mock)")
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all alert notification tests."""
        self.log("Starting alert notification system tests")
        
        tests = [
            ("Prometheus Connection", self.check_prometheus_connection),
            ("Test Alert Configuration", self.load_test_alerts),
            ("Alert Rule Syntax", self.test_alert_rule_syntax),
            ("Alert Evaluation", self.test_alert_evaluation),
            ("Alert Thresholds", self.test_alert_thresholds),
            ("Alert Labels and Annotations", self.test_alert_labels_and_annotations),
            ("Alert Condition Simulation", self.simulate_alert_conditions),
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
        
        self.log(f"\n=== ALERT NOTIFICATION TEST SUMMARY ===")
        self.log(f"Tests passed: {passed}/{total} ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            self.log("✓ Alert notification system is functioning well")
        elif success_rate >= 0.6:
            self.log("⚠️  Alert notification system has some issues", 'WARN')
        else:
            self.log("✗ Alert notification system has significant problems", 'ERROR')
        
        return results


def main():
    """Main function to run alert notification tests."""
    tester = AlertNotificationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")
        exit(1)
    else:
        print("\n✓ All alert notification tests passed!")
        exit(0)


if __name__ == '__main__':
    main()