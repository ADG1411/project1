#!/usr/bin/env python3
"""
MLOps Infrastructure Configuration Validator
This script validates all configuration files without requiring Docker.
"""

import json
import yaml
import os
import sys
from pathlib import Path

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

def validate_yaml_file(filepath):
    """Validate YAML file syntax"""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load(f)
        return True, "Valid YAML"
    except yaml.YAMLError as e:
        return False, f"YAML Error: {e}"
    except Exception as e:
        return False, f"File Error: {e}"

def validate_hcl_file(filepath):
    """Basic HCL file validation (syntax check)"""
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

def main():
    """Main validation function"""
    print("🔍 MLOps Infrastructure Configuration Validator")
    print("=" * 50)
    
    # Define files to validate
    validations = [
        # JSON files
        ("grafana/dashboard.json", validate_json_file),
        
        # YAML files  
        ("docker-compose.yml", validate_yaml_file),
        ("prometheus/prometheus.yml", validate_yaml_file),
        ("grafana/datasources.yml", validate_yaml_file),
        ("grafana/dashboards.yml", validate_yaml_file),
        
        # HCL files
        ("nomad/nomad.hcl", validate_hcl_file),
        ("consul/consul.hcl", validate_hcl_file),
        
        # Python files
        ("app/train.py", validate_python_file),
        
        # Dockerfile
        ("app/Dockerfile", validate_dockerfile),
    ]
    
    all_valid = True
    results = []
    
    for filepath, validator in validations:
        if os.path.exists(filepath):
            is_valid, message = validator(filepath)
            status = "✅ PASS" if is_valid else "❌ FAIL"
            results.append((filepath, status, message))
            
            if not is_valid:
                all_valid = False
        else:
            results.append((filepath, "❌ MISSING", "File not found"))
            all_valid = False
    
    # Print results
    print("\n📋 Validation Results:")
    print("-" * 70)
    for filepath, status, message in results:
        print(f"{status:<8} {filepath:<30} {message}")
    
    # Check for required directories
    print("\n📁 Directory Structure Check:")
    print("-" * 70)
    required_dirs = ["app", "consul", "grafana", "nomad", "prometheus"]
    for dirname in required_dirs:
        if os.path.exists(dirname) and os.path.isdir(dirname):
            print(f"✅ PASS   {dirname}/")
        else:
            print(f"❌ MISSING {dirname}/")
            all_valid = False
    
    # Check for required files
    print(f"\n📄 File Count Check:")
    print("-" * 70)
    total_files = len([f for f, _, _ in validations if os.path.exists(f)])
    expected_files = len(validations)
    print(f"Files Found: {total_files}/{expected_files}")
    
    # Final status
    print(f"\n🎯 Overall Status:")
    print("-" * 70)
    if all_valid:
        print("✅ ALL CONFIGURATIONS VALID - Ready for deployment!")
        print("\n🚀 To deploy:")
        print("   docker-compose build ml-trainer")
        print("   docker-compose up -d")
        return 0
    else:
        print("❌ CONFIGURATION ISSUES FOUND - Please fix errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())