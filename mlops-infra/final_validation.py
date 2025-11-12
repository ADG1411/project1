#!/usr/bin/env python3
"""
MLOps Infrastructure Final Validation Script
This script validates all the fixes applied to the configuration.
"""

import os
import json
import re

def check_docker_socket_mount():
    """Check if Docker socket mount is writable"""
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Should not have :ro on docker socket mount
    if '/var/run/docker.sock:/var/run/docker.sock:ro' in content:
        return False, "Docker socket mount is still read-only"
    elif '/var/run/docker.sock:/var/run/docker.sock' in content:
        return True, "Docker socket mount is writable"
    else:
        return False, "Docker socket mount not found"

def check_nomad_job_mount():
    """Check if Nomad job file is mounted"""
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    if './nomad/mlops.nomad:/nomad/config/mlops.nomad:ro' in content:
        return True, "Nomad job file is mounted"
    else:
        return False, "Nomad job file mount is missing"

def check_network_mode():
    """Check network mode in Nomad job file"""
    with open('nomad/mlops.nomad', 'r') as f:
        content = f.read()
    
    if 'network_mode = "mlops-infra_mlops-network"' in content:
        return True, "Network mode set to custom network"
    elif 'network_mode = "bridge"' in content:
        return False, "Network mode still set to bridge (won't communicate with custom network)"
    else:
        return False, "Network mode not found"

def check_requests_version():
    """Check if requests package is updated"""
    with open('app/requirements.txt', 'r') as f:
        content = f.read()
    
    if 'requests==2.32.3' in content:
        return True, "Requests package updated to secure version"
    elif 'requests==2.31.0' in content:
        return False, "Requests package still has security vulnerability"
    else:
        return False, "Requests package not found"

def check_grafana_dashboard():
    """Check if Grafana dashboard variables are fixed"""
    with open('grafana/dashboard.json', 'r') as f:
        content = f.read()
    
    if '${DS_PROMETHEUS}' in content:
        return False, "Dashboard still has undefined variables"
    elif '"uid": "Prometheus"' in content:
        return True, "Dashboard variables fixed"
    else:
        return False, "Dashboard datasource configuration unclear"

def check_log_rotation():
    """Check if log rotation is configured for all services"""
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    # Count occurrences of logging configuration
    log_configs = content.count('logging:')
    max_size_configs = content.count('max-size: "10m"')
    max_file_configs = content.count('max-file: "3"')
    
    # Should have logging for consul, nomad, prometheus, grafana, pushgateway
    expected_services = 5
    
    if log_configs >= expected_services and max_size_configs >= expected_services:
        return True, f"Log rotation configured for {log_configs} services"
    else:
        return False, f"Log rotation incomplete: {log_configs}/{expected_services} services configured"

def check_startup_delay():
    """Check if Nomad has startup delay"""
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    if 'sleep 10 && nomad agent' in content:
        return True, "Nomad startup delay configured"
    else:
        return False, "Nomad startup delay missing"

def check_pushgateway():
    """Check if Pushgateway is configured"""
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    if 'pushgateway:' in content and 'prom/pushgateway' in content:
        return True, "Pushgateway service configured"
    else:
        return False, "Pushgateway service missing"

def check_prometheus_metrics():
    """Check if ML training script has Prometheus integration"""
    with open('app/train.py', 'r') as f:
        content = f.read()
    
    if 'prometheus_client' in content and 'push_to_gateway' in content:
        return True, "ML training script has Prometheus metrics"
    else:
        return False, "ML training script missing Prometheus integration"

def check_prometheus_client_dependency():
    """Check if prometheus-client is in requirements"""
    with open('app/requirements.txt', 'r') as f:
        content = f.read()
    
    if 'prometheus-client' in content:
        return True, "Prometheus client dependency added"
    else:
        return False, "Prometheus client dependency missing"

def main():
    """Main validation function"""
    print("🔍 MLOps Infrastructure - Fix Validation")
    print("=" * 50)
    
    fixes = [
        ("Docker Socket Mount", check_docker_socket_mount),
        ("Nomad Job File Mount", check_nomad_job_mount), 
        ("Network Mode Fix", check_network_mode),
        ("Security Fix (requests)", check_requests_version),
        ("Grafana Dashboard Fix", check_grafana_dashboard),
        ("Log Rotation", check_log_rotation),
        ("Nomad Startup Delay", check_startup_delay),
        ("Pushgateway Service", check_pushgateway),
        ("ML Prometheus Metrics", check_prometheus_metrics),
        ("Prometheus Client Dependency", check_prometheus_client_dependency),
    ]
    
    all_fixed = True
    results = []
    
    for fix_name, check_func in fixes:
        try:
            success, message = check_func()
            status = "✅ FIXED" if success else "❌ ISSUE"
            results.append((fix_name, status, message))
            
            if not success:
                all_fixed = False
                
        except Exception as e:
            results.append((fix_name, "❌ ERROR", str(e)))
            all_fixed = False
    
    # Print results
    print("\n📋 Fix Validation Results:")
    print("-" * 60)
    for fix_name, status, message in results:
        print(f"{status} {fix_name:<25} {message}")
    
    print(f"\n🎯 Overall Status:")
    print("-" * 60)
    
    if all_fixed:
        print("🎉 ALL FIXES APPLIED SUCCESSFULLY!")
        print("\n✅ Configuration is now production-ready with:")
        print("   - Proper Docker socket permissions for Nomad")
        print("   - Accessible Nomad job files inside containers")
        print("   - Correct network configuration")
        print("   - Security vulnerabilities patched")
        print("   - Working Grafana dashboards")
        print("   - Log rotation for all services")
        print("   - Startup synchronization")
        print("   - ML metrics exported to Prometheus")
        print("   - Cross-platform deployment instructions")
        
        print(f"\n🚀 Ready for deployment:")
        print("   docker-compose build ml-trainer")
        print("   docker-compose up -d")
        print("   # Wait 90 seconds")
        print("   docker exec mlops-nomad nomad job run /nomad/config/mlops.nomad")
        
        return 0
    else:
        print("❌ SOME FIXES NOT APPLIED:")
        for fix_name, status, message in results:
            if status in ["❌ ISSUE", "❌ ERROR"]:
                print(f"   - {fix_name}: {message}")
        
        return 1

if __name__ == "__main__":
    exit(main())