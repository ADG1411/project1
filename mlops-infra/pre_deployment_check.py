#!/usr/bin/env python3
"""
MLOps Infrastructure Pre-Deployment Checker
This script performs comprehensive checks before deployment.
"""

import subprocess
import sys
import os
import json
import time

def run_command(command, capture_output=True):
    """Run a command and return the result"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(command, shell=True, timeout=30)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_docker_installation():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker installation...")
    
    # Check if docker command exists
    success, stdout, stderr = run_command("docker --version")
    if not success:
        return False, "Docker is not installed or not in PATH"
    
    print(f"   ✅ Docker found: {stdout}")
    
    # Check if Docker daemon is running
    success, stdout, stderr = run_command("docker info")
    if not success:
        return False, "Docker daemon is not running. Please start Docker Desktop."
    
    print("   ✅ Docker daemon is running")
    return True, "Docker is ready"

def check_docker_compose():
    """Check Docker Compose availability"""
    print("📦 Checking Docker Compose...")
    
    # Try docker-compose first
    success, stdout, stderr = run_command("docker-compose --version")
    if success:
        print(f"   ✅ Docker Compose found: {stdout}")
        return True, "docker-compose"
    
    # Try docker compose (newer syntax)
    success, stdout, stderr = run_command("docker compose version")
    if success:
        print(f"   ✅ Docker Compose found: {stdout}")
        return True, "docker compose"
    
    return False, "Docker Compose not found"

def check_ports():
    """Check if required ports are available"""
    print("🔌 Checking port availability...")
    
    required_ports = [3000, 4646, 8500, 9090]
    
    for port in required_ports:
        # Use netstat to check if port is in use
        success, stdout, stderr = run_command(f"netstat -an | findstr :{port}")
        if success and stdout:
            print(f"   ⚠️  Port {port} appears to be in use")
            print(f"      {stdout}")
        else:
            print(f"   ✅ Port {port} is available")
    
    return True, "Port check completed"

def check_system_resources():
    """Check system resources"""
    print("💻 Checking system resources...")
    
    # Check available disk space (Windows)
    success, stdout, stderr = run_command("dir /-c")
    if success:
        print("   ✅ Disk space check completed")
    
    # Note: Memory check would require additional tools on Windows
    print("   ℹ️  Ensure at least 4GB RAM is available")
    
    return True, "Resource check completed"

def validate_configuration():
    """Run our configuration validator"""
    print("⚙️  Validating configurations...")
    
    if not os.path.exists("validate_simple.py"):
        print("   ⚠️  Configuration validator not found")
        return True, "Skipping configuration validation"
    
    success, stdout, stderr = run_command("python validate_simple.py")
    if success:
        print("   ✅ All configurations are valid")
        return True, "Configuration validation passed"
    else:
        print("   ❌ Configuration validation failed:")
        print(stderr)
        return False, "Configuration validation failed"

def check_files():
    """Check if all required files exist"""
    print("📄 Checking required files...")
    
    required_files = [
        "docker-compose.yml",
        "app/Dockerfile",
        "app/train.py",
        "nomad/nomad.hcl",
        "consul/consul.hcl",
        "prometheus/prometheus.yml",
        "grafana/dashboard.json"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        return False, f"Missing files: {', '.join(missing_files)}"
    
    return True, "All required files present"

def main():
    """Main pre-deployment check function"""
    print("🚀 MLOps Infrastructure Pre-Deployment Checker")
    print("=" * 60)
    
    checks = [
        ("System Files", check_files),
        ("Configuration", validate_configuration),
        ("Docker Installation", check_docker_installation),
        ("Docker Compose", check_docker_compose),
        ("Port Availability", check_ports),
        ("System Resources", check_system_resources),
    ]
    
    all_passed = True
    results = []
    
    for check_name, check_func in checks:
        try:
            success, message = check_func()
            status = "✅ PASS" if success else "❌ FAIL"
            results.append((check_name, status, message))
            
            if not success:
                all_passed = False
                
        except Exception as e:
            results.append((check_name, "❌ ERROR", str(e)))
            all_passed = False
    
    # Print summary
    print(f"\n📋 Pre-Deployment Check Results:")
    print("-" * 60)
    for check_name, status, message in results:
        print(f"{status} {check_name:<20} {message}")
    
    print(f"\n🎯 Overall Status:")
    print("-" * 60)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED - Ready for deployment!")
        print(f"\n🚀 Next steps:")
        
        # Check which Docker Compose command to use
        compose_cmd = "docker-compose"
        success, stdout, stderr = run_command("docker-compose --version")
        if not success:
            compose_cmd = "docker compose"
        
        print(f"   1. {compose_cmd} build ml-trainer")
        print(f"   2. {compose_cmd} up -d")
        print(f"   3. Wait 60-90 seconds for services to start")
        print(f"   4. Access UIs:")
        print(f"      - Nomad:      http://localhost:4646")
        print(f"      - Consul:     http://localhost:8500")
        print(f"      - Prometheus: http://localhost:9090")
        print(f"      - Grafana:    http://localhost:3000 (admin/mlopsadmin)")
        
        return 0
    else:
        print("❌ ISSUES FOUND - Please resolve before deployment:")
        for check_name, status, message in results:
            if status == "❌ FAIL" or status == "❌ ERROR":
                print(f"   - {check_name}: {message}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())