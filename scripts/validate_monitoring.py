#!/usr/bin/env python3
"""
Simple monitoring validation script.

This script performs basic validation of the monitoring system components
without requiring all services to be running.
"""

import json
import yaml
import os
import sys
from pathlib import Path


def validate_prometheus_config():
    """Validate Prometheus configuration."""
    print("✓ Validating Prometheus configuration...")
    
    try:
        with open('monitoring/prometheus.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['global', 'scrape_configs', 'rule_files']
        for section in required_sections:
            if section not in config:
                print(f"✗ Missing section: {section}")
                return False
        
        # Check scrape configs
        scrape_configs = config['scrape_configs']
        expected_jobs = ['prometheus', 'django-api', 'nextjs-web', 'node-exporter']
        
        found_jobs = [job['job_name'] for job in scrape_configs]
        for job in expected_jobs:
            if job in found_jobs:
                print(f"  ✓ Found scrape config for: {job}")
            else:
                print(f"  ⚠ Missing scrape config for: {job}")
        
        print("✓ Prometheus configuration is valid")
        return True
        
    except Exception as e:
        print(f"✗ Error validating Prometheus config: {e}")
        return False


def validate_alerting_rules():
    """Validate alerting rules configuration."""
    print("✓ Validating alerting rules...")
    
    try:
        with open('monitoring/prometheus-alerts.yml', 'r') as f:
            alerts = yaml.safe_load(f)
        
        if 'groups' not in alerts:
            print("✗ No alert groups found")
            return False
        
        total_rules = 0
        valid_rules = 0
        
        for group in alerts['groups']:
            if 'rules' not in group:
                continue
                
            for rule in group['rules']:
                total_rules += 1
                
                # Check required fields for alert rules
                if 'alert' in rule:
                    required_fields = ['expr', 'labels', 'annotations']
                    if all(field in rule for field in required_fields):
                        valid_rules += 1
                        
                        # Check severity
                        if 'severity' in rule['labels']:
                            severity = rule['labels']['severity']
                            if severity in ['critical', 'warning', 'info']:
                                print(f"  ✓ Alert: {rule['alert']} ({severity})")
                            else:
                                print(f"  ⚠ Alert: {rule['alert']} has invalid severity: {severity}")
                        else:
                            print(f"  ⚠ Alert: {rule['alert']} missing severity label")
                    else:
                        print(f"  ✗ Alert: {rule.get('alert', 'unknown')} missing required fields")
        
        print(f"✓ Alerting rules: {valid_rules}/{total_rules} valid")
        return valid_rules == total_rules
        
    except Exception as e:
        print(f"✗ Error validating alerting rules: {e}")
        return False


def validate_grafana_dashboards():
    """Validate Grafana dashboard configurations."""
    print("✓ Validating Grafana dashboards...")
    
    dashboard_dir = Path('monitoring/grafana/dashboards')
    if not dashboard_dir.exists():
        print("✗ Grafana dashboards directory not found")
        return False
    
    dashboard_files = list(dashboard_dir.glob('*.json'))
    if not dashboard_files:
        print("✗ No dashboard files found")
        return False
    
    valid_dashboards = 0
    
    for dashboard_file in dashboard_files:
        try:
            with open(dashboard_file, 'r') as f:
                dashboard_config = json.load(f)
            
            if 'dashboard' not in dashboard_config:
                print(f"  ✗ {dashboard_file.name}: Invalid structure")
                continue
            
            dashboard = dashboard_config['dashboard']
            
            # Check required fields
            if 'title' not in dashboard or 'panels' not in dashboard:
                print(f"  ✗ {dashboard_file.name}: Missing title or panels")
                continue
            
            # Count panels with queries
            panels_with_queries = 0
            total_panels = 0
            
            for panel in dashboard['panels']:
                if panel.get('type') != 'row':  # Skip row panels
                    total_panels += 1
                    if 'targets' in panel:
                        for target in panel['targets']:
                            if 'expr' in target:
                                panels_with_queries += 1
                                break
            
            print(f"  ✓ {dashboard_file.name}: {panels_with_queries}/{total_panels} panels with queries")
            valid_dashboards += 1
            
        except Exception as e:
            print(f"  ✗ {dashboard_file.name}: Error - {e}")
    
    print(f"✓ Grafana dashboards: {valid_dashboards}/{len(dashboard_files)} valid")
    return valid_dashboards == len(dashboard_files)


def validate_docker_compose():
    """Validate Docker Compose monitoring services."""
    print("✓ Validating Docker Compose monitoring services...")
    
    try:
        with open('docker-compose.yml', 'r') as f:
            compose_config = yaml.safe_load(f)
        
        if 'services' not in compose_config:
            print("✗ No services found in docker-compose.yml")
            return False
        
        services = compose_config['services']
        
        # Check monitoring services
        monitoring_services = [
            'prometheus',
            'grafana',
            'node-exporter',
            'elasticsearch',
            'logstash',
            'kibana'
        ]
        
        found_services = []
        for service in monitoring_services:
            if service in services:
                found_services.append(service)
                print(f"  ✓ Found service: {service}")
            else:
                print(f"  ⚠ Missing service: {service}")
        
        # Check if services have proper configuration
        if 'prometheus' in services:
            prometheus_service = services['prometheus']
            if 'volumes' in prometheus_service:
                volumes = prometheus_service['volumes']
                config_mounted = any('prometheus.yml' in vol for vol in volumes)
                alerts_mounted = any('prometheus-alerts.yml' in vol for vol in volumes)
                
                if config_mounted and alerts_mounted:
                    print("  ✓ Prometheus configuration files mounted")
                else:
                    print("  ⚠ Prometheus configuration files not properly mounted")
        
        print(f"✓ Docker Compose: {len(found_services)}/{len(monitoring_services)} monitoring services configured")
        return len(found_services) >= len(monitoring_services) * 0.75  # 75% threshold
        
    except Exception as e:
        print(f"✗ Error validating Docker Compose: {e}")
        return False


def validate_metrics_implementation():
    """Validate metrics implementation files."""
    print("✓ Validating metrics implementation...")
    
    # Check backend metrics
    backend_metrics_file = Path('api/koroh_platform/utils/metrics.py')
    if backend_metrics_file.exists():
        print("  ✓ Backend metrics implementation found")
        
        # Check for key metrics
        with open(backend_metrics_file, 'r') as f:
            content = f.read()
            
        key_metrics = [
            'ai_requests_total',
            'cv_uploads_total',
            'portfolio_generations_total',
            'active_users_gauge',
            'celery_tasks_processed'
        ]
        
        found_metrics = []
        for metric in key_metrics:
            if metric in content:
                found_metrics.append(metric)
                print(f"    ✓ Found metric: {metric}")
            else:
                print(f"    ⚠ Missing metric: {metric}")
        
        backend_valid = len(found_metrics) >= len(key_metrics) * 0.8
    else:
        print("  ✗ Backend metrics implementation not found")
        backend_valid = False
    
    # Check frontend metrics
    frontend_metrics_file = Path('web/lib/metrics.ts')
    if frontend_metrics_file.exists():
        print("  ✓ Frontend metrics implementation found")
        
        with open(frontend_metrics_file, 'r') as f:
            content = f.read()
        
        key_functions = [
            'trackPageView',
            'trackUserInteraction',
            'trackFeatureUsage',
            'trackClientError'
        ]
        
        found_functions = []
        for func in key_functions:
            if func in content:
                found_functions.append(func)
                print(f"    ✓ Found function: {func}")
            else:
                print(f"    ⚠ Missing function: {func}")
        
        frontend_valid = len(found_functions) >= len(key_functions) * 0.8
    else:
        print("  ✗ Frontend metrics implementation not found")
        frontend_valid = False
    
    # Check metrics API endpoint
    metrics_endpoint = Path('web/app/api/metrics/route.ts')
    if metrics_endpoint.exists():
        print("  ✓ Metrics API endpoint found")
        endpoint_valid = True
    else:
        print("  ✗ Metrics API endpoint not found")
        endpoint_valid = False
    
    return backend_valid and frontend_valid and endpoint_valid


def main():
    """Run all validation checks."""
    print("🔍 Validating Koroh Platform Monitoring System")
    print("=" * 50)
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    validations = [
        ("Prometheus Configuration", validate_prometheus_config),
        ("Alerting Rules", validate_alerting_rules),
        ("Grafana Dashboards", validate_grafana_dashboards),
        ("Docker Compose Services", validate_docker_compose),
        ("Metrics Implementation", validate_metrics_implementation),
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validation_func in validations:
        print(f"\n📋 {name}")
        print("-" * 30)
        
        try:
            if validation_func():
                passed += 1
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    success_rate = passed / total
    print(f"Tests passed: {passed}/{total} ({success_rate:.1%})")
    
    if success_rate >= 0.9:
        print("🎉 Monitoring system is well configured!")
        exit_code = 0
    elif success_rate >= 0.7:
        print("⚠️  Monitoring system has minor issues")
        exit_code = 0
    else:
        print("🚨 Monitoring system has significant issues")
        exit_code = 1
    
    print("\n💡 Next steps:")
    if success_rate < 1.0:
        print("- Fix the failed validation checks above")
    print("- Start the monitoring services with: make dev")
    print("- Run integration tests with: python scripts/test_monitoring_integration.py")
    print("- Access Grafana at: http://localhost:3001")
    print("- Access Prometheus at: http://localhost:9090")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()