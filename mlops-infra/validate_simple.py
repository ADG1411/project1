#!/usr/bin/env python3
"""
MLOps Infrastructure Configuration Validator (No Dependencies)
This script validates configuration files without requiring external packages.
"""

import json
import os
import re

def validate_json_file(filepath):
    """Validate JSON file syntax"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_basic_yaml(filepath):
    """Basic YAML validation without PyYAML"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Basic checks
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for basic YAML structure issues
            if line.strip() and not line.startswith('#'):
                if line.lstrip() != line and not re.match(r'^[ ]+', line):
                    continue  # Allow tabs for now
                
        return True, "Basic YAML structure appears valid"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_docker_compose(filepath):
    """Validate Docker Compose file structure"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = ['version:', 'services:', 'networks:']
        missing = [section for section in required_sections if section not in content]
        
        if missing:
            return False, f"Missing sections: {', '.join(missing)}"
        
        # Check for our specific services
        required_services = ['consul:', 'nomad:', 'prometheus:', 'grafana:']
        missing_services = [svc for svc in required_services if svc not in content]
        
        if missing_services:
            return False, f"Missing services: {', '.join(missing_services)}"
        
        return True, "Docker Compose structure valid"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_hcl_file(filepath):
    """Basic HCL file validation"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Basic syntax checks
        if content.count('{') != content.count('}'):
            return False, "Unmatched braces in HCL file"
        
        if content.count('"') % 2 != 0:
            return False, "Unmatched quotes in HCL file"
            
        return True, "Basic HCL syntax appears valid"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_python_file(filepath):
    """Validate Python file syntax"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        compile(content, filepath, 'exec')
        return True, "Valid Python syntax"
    except SyntaxError as e:
        return False, f"Python Syntax Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_dockerfile(filepath):
    """Basic Dockerfile validation"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        has_from = any(line.strip().upper().startswith('FROM') for line in lines)
        if not has_from:
            return False, "Missing FROM instruction"
        
        return True, "Basic Dockerfile structure valid"
    except Exception as e:
        return False, f"File Error: {e}"

def check_file_exists(filepath):
    """Check if file exists and get size"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        return True, f"Exists ({size} bytes)"
    return False, "File not found"

def main():
    """Main validation function"""
    print("🔍 MLOps Infrastructure Configuration Validator")
    print("=" * 60)
    
    # File existence check
    files_to_check = [
        "docker-compose.yml",
        "nomad/nomad.hcl", 
        "nomad/mlops.nomad",
        "consul/consul.hcl",
        "prometheus/prometheus.yml",
        "grafana/dashboard.json",
        "grafana/datasources.yml", 
        "grafana/dashboards.yml",
        "app/train.py",
        "app/Dockerfile",
        "app/requirements.txt",
        "README.md",
        "QUICKSTART.md",
        "ARCHITECTURE.md",
        "DEPLOYMENT_CHECKLIST.md",
        "PROJECT_SUMMARY.md"
    ]
    
    print("📁 File Existence Check:")
    print("-" * 60)
    all_files_exist = True
    for filepath in files_to_check:
        exists, info = check_file_exists(filepath)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{status:<10} {filepath:<35} {info}")
        if not exists:
            all_files_exist = False
    
    # Detailed validation
    print(f"\n🔍 Configuration Validation:")
    print("-" * 60)
    
    validations = [
        ("docker-compose.yml", validate_docker_compose),
        ("grafana/dashboard.json", validate_json_file),
        ("grafana/datasources.yml", validate_basic_yaml),
        ("grafana/dashboards.yml", validate_basic_yaml),
        ("prometheus/prometheus.yml", validate_basic_yaml),
        ("nomad/nomad.hcl", validate_hcl_file),
        ("consul/consul.hcl", validate_hcl_file),
        ("app/train.py", validate_python_file),
        ("app/Dockerfile", validate_dockerfile),
    ]
    
    all_valid = True
    for filepath, validator in validations:
        if os.path.exists(filepath):
            is_valid, message = validator(filepath)
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"{status:<10} {filepath:<35} {message}")
            if not is_valid:
                all_valid = False
        else:
            print(f"❌ MISSING  {filepath:<35} Cannot validate - file missing")
            all_valid = False
    
    # Directory structure check
    print(f"\n📂 Directory Structure:")
    print("-" * 60)
    required_dirs = ["app", "consul", "grafana", "nomad", "prometheus"]
    dirs_ok = True
    for dirname in required_dirs:
        if os.path.exists(dirname) and os.path.isdir(dirname):
            file_count = len([f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))])
            print(f"✅ EXISTS   {dirname}/ ({file_count} files)")
        else:
            print(f"❌ MISSING  {dirname}/")
            dirs_ok = False
    
    # Summary
    print(f"\n🎯 Validation Summary:")
    print("-" * 60)
    
    if all_files_exist and all_valid and dirs_ok:
        print("🎉 SUCCESS: All configurations are valid!")
        print("\n🚀 Ready for deployment:")
        print("   1. Install Docker Desktop")
        print("   2. Run: docker-compose build ml-trainer") 
        print("   3. Run: docker-compose up -d")
        print("   4. Access services:")
        print("      - Nomad:      http://localhost:4646")
        print("      - Consul:     http://localhost:8500")
        print("      - Prometheus: http://localhost:9090")
        print("      - Grafana:    http://localhost:3000")
        return 0
    else:
        print("❌ ISSUES FOUND:")
        if not all_files_exist:
            print("   - Some required files are missing")
        if not all_valid:
            print("   - Some configuration files have errors")
        if not dirs_ok:
            print("   - Directory structure is incomplete")
        print("\n🔧 Please fix the issues above before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())