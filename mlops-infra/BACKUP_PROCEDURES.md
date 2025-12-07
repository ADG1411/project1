# Backup and Restore Procedures

## Overview
This document provides comprehensive backup and restore procedures for all MLOps infrastructure components including data volumes, configurations, and application state.

## Data Volumes Backup

### Manual Backup Commands

#### 1. Prometheus Data Backup
```bash
# Create backup directory
mkdir -p ./backups/prometheus/$(date +%Y%m%d_%H%M%S)

# Stop Prometheus service
docker-compose stop prometheus

# Create compressed backup
docker run --rm -v mlops-infra_prometheus-data:/data -v $(pwd)/backups/prometheus/$(date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/prometheus-data.tar.gz -C /data .

# Restart Prometheus
docker-compose start prometheus
```

#### 2. Grafana Data Backup
```bash
# Create backup directory
mkdir -p ./backups/grafana/$(date +%Y%m%d_%H%M%S)

# Stop Grafana service
docker-compose stop grafana

# Create compressed backup
docker run --rm -v mlops-infra_grafana-data:/data -v $(pwd)/backups/grafana/$(date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/grafana-data.tar.gz -C /data .

# Restart Grafana
docker-compose start grafana
```

#### 3. Consul Data Backup
```bash
# Create backup directory
mkdir -p ./backups/consul/$(date +%Y%m%d_%H%M%S)

# Stop Consul service
docker-compose stop consul

# Create compressed backup
docker run --rm -v mlops-infra_consul-data:/data -v $(pwd)/backups/consul/$(date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/consul-data.tar.gz -C /data .

# Restart Consul
docker-compose start consul
```

#### 4. Nomad Data Backup
```bash
# Create backup directory
mkdir -p ./backups/nomad/$(date +%Y%m%d_%H%M%S)

# Stop Nomad service
docker-compose stop nomad

# Create compressed backup
docker run --rm -v mlops-infra_nomad-data:/data -v $(pwd)/backups/nomad/$(date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/nomad-data.tar.gz -C /data .

# Restart Nomad
docker-compose start nomad
```

### Complete System Backup
```bash
#!/bin/bash
# complete_backup.sh
set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="./backups/$BACKUP_DATE"

echo "Starting complete MLOps infrastructure backup: $BACKUP_DATE"

# Create backup directories
mkdir -p "$BACKUP_ROOT"/{prometheus,grafana,consul,nomad,configs}

# Stop all services
echo "Stopping services..."
docker-compose stop

# Backup all volumes
echo "Backing up Prometheus data..."
docker run --rm -v mlops-infra_prometheus-data:/data -v $(pwd)/$BACKUP_ROOT/prometheus:/backup alpine tar czf /backup/prometheus-data.tar.gz -C /data .

echo "Backing up Grafana data..."
docker run --rm -v mlops-infra_grafana-data:/data -v $(pwd)/$BACKUP_ROOT/grafana:/backup alpine tar czf /backup/grafana-data.tar.gz -C /data .

echo "Backing up Consul data..."
docker run --rm -v mlops-infra_consul-data:/data -v $(pwd)/$BACKUP_ROOT/consul:/backup alpine tar czf /backup/consul-data.tar.gz -C /data .

echo "Backing up Nomad data..."
docker run --rm -v mlops-infra_nomad-data:/data -v $(pwd)/$BACKUP_ROOT/nomad:/backup alpine tar czf /backup/nomad-data.tar.gz -C /data .

# Backup configuration files
echo "Backing up configurations..."
cp -r ./consul/ "$BACKUP_ROOT/configs/"
cp -r ./grafana/ "$BACKUP_ROOT/configs/"
cp -r ./nomad/ "$BACKUP_ROOT/configs/"
cp -r ./prometheus/ "$BACKUP_ROOT/configs/"
cp -r ./app/ "$BACKUP_ROOT/configs/"
cp docker-compose.yml "$BACKUP_ROOT/configs/"
cp .env "$BACKUP_ROOT/configs/" 2>/dev/null || echo "No .env file found"

# Create manifest
cat > "$BACKUP_ROOT/manifest.json" << EOF
{
  "backup_timestamp": "$BACKUP_DATE",
  "backup_type": "complete_system",
  "components": {
    "prometheus": {
      "data_file": "prometheus/prometheus-data.tar.gz",
      "config_dir": "configs/prometheus/"
    },
    "grafana": {
      "data_file": "grafana/grafana-data.tar.gz",
      "config_dir": "configs/grafana/"
    },
    "consul": {
      "data_file": "consul/consul-data.tar.gz",
      "config_dir": "configs/consul/"
    },
    "nomad": {
      "data_file": "nomad/nomad-data.tar.gz",
      "config_dir": "configs/nomad/"
    }
  },
  "docker_compose": "configs/docker-compose.yml",
  "environment": "configs/.env"
}
EOF

# Restart services
echo "Restarting services..."
docker-compose up -d

echo "Backup completed: $BACKUP_ROOT"
echo "Backup size: $(du -sh $BACKUP_ROOT | cut -f1)"
```

## Restore Procedures

### Complete System Restore
```bash
#!/bin/bash
# restore_system.sh
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20231201_143022"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_ROOT="./backups/$BACKUP_DATE"

if [ ! -d "$BACKUP_ROOT" ]; then
    echo "Backup directory not found: $BACKUP_ROOT"
    exit 1
fi

echo "Starting system restore from backup: $BACKUP_DATE"

# Stop all services
echo "Stopping services..."
docker-compose down -v

# Remove existing volumes
echo "Removing existing volumes..."
docker volume rm mlops-infra_prometheus-data mlops-infra_grafana-data mlops-infra_consul-data mlops-infra_nomad-data 2>/dev/null || true

# Restore volumes
echo "Restoring Prometheus data..."
docker volume create mlops-infra_prometheus-data
docker run --rm -v mlops-infra_prometheus-data:/data -v $(pwd)/$BACKUP_ROOT/prometheus:/backup alpine tar xzf /backup/prometheus-data.tar.gz -C /data

echo "Restoring Grafana data..."
docker volume create mlops-infra_grafana-data
docker run --rm -v mlops-infra_grafana-data:/data -v $(pwd)/$BACKUP_ROOT/grafana:/backup alpine tar xzf /backup/grafana-data.tar.gz -C /data

echo "Restoring Consul data..."
docker volume create mlops-infra_consul-data
docker run --rm -v mlops-infra_consul-data:/data -v $(pwd)/$BACKUP_ROOT/consul:/backup alpine tar xzf /backup/consul-data.tar.gz -C /data

echo "Restoring Nomad data..."
docker volume create mlops-infra_nomad-data
docker run --rm -v mlops-infra_nomad-data:/data -v $(pwd)/$BACKUP_ROOT/nomad:/backup alpine tar xzf /backup/nomad-data.tar.gz -C /data

# Restore configurations
echo "Restoring configurations..."
cp -r "$BACKUP_ROOT/configs/"* ./

# Start services
echo "Starting services..."
docker-compose up -d

echo "System restore completed from backup: $BACKUP_DATE"
```

## Automated Backup Cronjob

### Daily Backup Cron Job
```bash
# Add to crontab: crontab -e
# Daily backup at 2 AM
0 2 * * * /path/to/mlops-infra/scripts/daily_backup.sh >> /var/log/mlops-backup.log 2>&1

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /path/to/mlops-infra/scripts/complete_backup.sh >> /var/log/mlops-backup.log 2>&1
```

### Daily Backup Script
```bash
#!/bin/bash
# scripts/daily_backup.sh
set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="./backups/daily/$BACKUP_DATE"
RETENTION_DAYS=7

echo "$(date): Starting daily backup: $BACKUP_DATE"

# Create backup directory
mkdir -p "$BACKUP_ROOT"

# Backup only data volumes (no service stop required)
echo "Backing up data volumes..."

# Prometheus (can be backed up while running)
docker run --rm -v mlops-infra_prometheus-data:/data -v $(pwd)/$BACKUP_ROOT:/backup alpine tar czf /backup/prometheus-data.tar.gz -C /data .

# Grafana (requires brief stop for consistency)
docker-compose stop grafana
docker run --rm -v mlops-infra_grafana-data:/data -v $(pwd)/$BACKUP_ROOT:/backup alpine tar czf /backup/grafana-data.tar.gz -C /data .
docker-compose start grafana

# Consul snapshot (using API)
curl -X GET "http://localhost:8500/v1/snapshot" --output "$BACKUP_ROOT/consul-snapshot.snap"

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find ./backups/daily/ -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

echo "$(date): Daily backup completed: $BACKUP_ROOT"
```

## Backup Validation

### Validation Script
```bash
#!/bin/bash
# validate_backup.sh
set -e

BACKUP_DIR=$1
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Validating backup: $BACKUP_DIR"

# Check manifest exists
if [ ! -f "$BACKUP_DIR/manifest.json" ]; then
    echo "ERROR: manifest.json not found"
    exit 1
fi

# Check data files exist
for component in prometheus grafana consul nomad; do
    data_file="$BACKUP_DIR/$component/${component}-data.tar.gz"
    if [ ! -f "$data_file" ]; then
        echo "ERROR: $data_file not found"
        exit 1
    fi
    
    # Check file is not empty
    if [ ! -s "$data_file" ]; then
        echo "ERROR: $data_file is empty"
        exit 1
    fi
    
    # Test archive integrity
    if ! tar -tzf "$data_file" >/dev/null 2>&1; then
        echo "ERROR: $data_file is corrupted"
        exit 1
    fi
    
    echo "✓ $component data file is valid"
done

echo "✓ Backup validation passed"
```

## Remote Backup Storage

### AWS S3 Backup
```bash
#!/bin/bash
# Upload backup to S3
aws s3 sync ./backups/ s3://your-mlops-backups/backups/ --exclude "*.tmp" --delete

# Download backup from S3
aws s3 sync s3://your-mlops-backups/backups/ ./backups/ --exclude "*.tmp"
```

### Google Cloud Storage Backup
```bash
#!/bin/bash
# Upload backup to GCS
gsutil -m rsync -r -d ./backups/ gs://your-mlops-backups/backups/

# Download backup from GCS
gsutil -m rsync -r -d gs://your-mlops-backups/backups/ ./backups/
```

## Monitoring Backup Health

### Backup Monitoring Script
```bash
#!/bin/bash
# monitor_backups.sh
set -e

BACKUP_DIR="./backups"
ALERT_THRESHOLD_HOURS=25  # Alert if no backup in 25 hours

# Find latest backup
LATEST_BACKUP=$(find $BACKUP_DIR -name "manifest.json" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2- | xargs dirname)

if [ -z "$LATEST_BACKUP" ]; then
    echo "CRITICAL: No backups found"
    exit 2
fi

# Check backup age
BACKUP_TIME=$(stat -c %Y "$LATEST_BACKUP/manifest.json")
CURRENT_TIME=$(date +%s)
HOURS_OLD=$(( (CURRENT_TIME - BACKUP_TIME) / 3600 ))

if [ $HOURS_OLD -gt $ALERT_THRESHOLD_HOURS ]; then
    echo "WARNING: Latest backup is $HOURS_OLD hours old (threshold: $ALERT_THRESHOLD_HOURS hours)"
    exit 1
fi

echo "OK: Latest backup is $HOURS_OLD hours old"
exit 0
```

## Recovery Testing

### Automated Recovery Test
```bash
#!/bin/bash
# recovery_test.sh
set -e

echo "Starting recovery test..."

# Create test environment
export COMPOSE_PROJECT_NAME=mlops-recovery-test
export COMPOSE_FILE=docker-compose.test.yml

# Use latest backup
LATEST_BACKUP=$(find ./backups -name "manifest.json" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2- | xargs dirname)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No backups found for recovery test"
    exit 1
fi

echo "Testing recovery from: $LATEST_BACKUP"

# Restore and start test environment
./scripts/restore_system.sh $(basename $LATEST_BACKUP)

# Wait for services to be healthy
sleep 30

# Test service endpoints
services=("consul:8500" "nomad:4646" "prometheus:9090" "grafana:3000")
for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    if curl -s -f "http://localhost:$port/api/health" >/dev/null 2>&1; then
        echo "✓ $name health check passed"
    else
        echo "✗ $name health check failed"
        exit 1
    fi
done

# Cleanup test environment
docker-compose -p mlops-recovery-test down -v

echo "✓ Recovery test passed"
```

## Best Practices

1. **Backup Frequency**: Daily incremental, weekly full backups
2. **Retention**: Keep 7 daily, 4 weekly, 12 monthly backups
3. **Validation**: Always validate backup integrity
4. **Testing**: Monthly recovery tests
5. **Monitoring**: Monitor backup age and size
6. **Security**: Encrypt backups for remote storage
7. **Documentation**: Maintain recovery runbooks
8. **Automation**: Use cron jobs for scheduled backups