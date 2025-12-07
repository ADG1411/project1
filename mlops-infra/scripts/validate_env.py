#!/usr/bin/env python3
"""
Environment Variables Validation Script
Validates that all required environment variables are properly configured.
"""

import os
import sys
import re
from typing import Dict, List, Optional

# Required environment variables and their validation rules
ENV_VARS = {
    'GRAFANA_ADMIN_PASSWORD': {
        'required': True,
        'min_length': 8,
        'description': 'Grafana admin password'
    },
    'MODEL_NAME': {
        'required': False,
        'pattern': r'^[a-zA-Z0-9_-]+$',
        'min_length': 3,
        'max_length': 50,
        'description': 'ML model name (alphanumeric, hyphens, underscores only)'
    },
    'TRAINING_EPOCHS': {
        'required': False,
        'type': 'int',
        'min_value': 1,
        'max_value': 1000,
        'description': 'Number of training epochs'
    },
    'HEALTH_CHECK_PORT': {
        'required': False,
        'type': 'int',
        'min_value': 1024,
        'max_value': 65535,
        'description': 'Health check server port'
    },
    'PUSHGATEWAY_TIMEOUT': {
        'required': False,
        'type': 'int',
        'min_value': 1,
        'max_value': 60,
        'description': 'Pushgateway timeout in seconds'
    }
}

def validate_env_var(name: str, value: Optional[str], config: Dict) -> List[str]:
    """Validate a single environment variable."""
    errors = []
    
    # Check if required
    if config.get('required', False) and not value:
        errors.append(f"{name} is required but not set")
        return errors
    
    # Skip validation if not set and not required
    if not value:
        return errors
    
    # Type validation
    var_type = config.get('type', 'str')
    if var_type == 'int':
        try:
            int_value = int(value)
            
            # Min value check
            if 'min_value' in config and int_value < config['min_value']:
                errors.append(f"{name} must be at least {config['min_value']}")
            
            # Max value check
            if 'max_value' in config and int_value > config['max_value']:
                errors.append(f"{name} must be at most {config['max_value']}")
        except ValueError:
            errors.append(f"{name} must be a valid integer")
            return errors
    
    # String validations
    if var_type == 'str':
        # Length validations
        if 'min_length' in config and len(value) < config['min_length']:
            errors.append(f"{name} must be at least {config['min_length']} characters long")
        
        if 'max_length' in config and len(value) > config['max_length']:
            errors.append(f"{name} must be at most {config['max_length']} characters long")
        
        # Pattern validation
        if 'pattern' in config:
            if not re.match(config['pattern'], value):
                errors.append(f"{name} does not match required pattern: {config['pattern']}")
    
    return errors

def validate_environment() -> bool:
    """Validate all environment variables."""
    print("Validating environment variables...")
    print("=" * 50)
    
    all_errors = []
    
    for var_name, config in ENV_VARS.items():
        value = os.getenv(var_name)
        errors = validate_env_var(var_name, value, config)
        
        if errors:
            print(f"❌ {var_name}: {', '.join(errors)}")
            all_errors.extend(errors)
        else:
            status = "✓ (set)" if value else "✓ (optional, not set)"
            print(f"✅ {var_name}: {status}")
    
    print("=" * 50)
    
    if all_errors:
        print(f"❌ Environment validation failed with {len(all_errors)} error(s)")
        return False
    else:
        print("✅ All environment variables are valid")
        return True

def print_env_documentation():
    """Print documentation for all environment variables."""
    print("\nEnvironment Variables Documentation:")
    print("=" * 50)
    
    for var_name, config in ENV_VARS.items():
        print(f"\n{var_name}:")
        print(f"  Description: {config.get('description', 'No description available')}")
        print(f"  Required: {'Yes' if config.get('required', False) else 'No'}")
        
        if config.get('type') == 'int':
            constraints = []
            if 'min_value' in config:
                constraints.append(f"min: {config['min_value']}")
            if 'max_value' in config:
                constraints.append(f"max: {config['max_value']}")
            if constraints:
                print(f"  Constraints: {', '.join(constraints)}")
        else:
            constraints = []
            if 'min_length' in config:
                constraints.append(f"min length: {config['min_length']}")
            if 'max_length' in config:
                constraints.append(f"max length: {config['max_length']}")
            if 'pattern' in config:
                constraints.append(f"pattern: {config['pattern']}")
            if constraints:
                print(f"  Constraints: {', '.join(constraints)}")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print_env_documentation()
        return 0
    
    success = validate_environment()
    
    if not success:
        print("\nFor detailed information about environment variables, run:")
        print("python scripts/validate_env.py --help")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())