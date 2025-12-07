# High Availability (HA) Production Architecture

## Overview
This document outlines the production High Availability architecture for the MLOps infrastructure, designed for 3-5 node clusters with redundancy, fault tolerance, and scalability.

## Architecture Components

### 1. Multi-Node Cluster Architecture

#### 3-Node Minimum HA Setup
```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │   HAProxy   │  │    Nginx    │  │   CloudFlare    │    │
│  │ (Primary)   │  │ (Secondary) │  │    (CDN/WAF)    │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane Nodes                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │   Node-1    │  │   Node-2    │  │     Node-3      │    │
│  │ (Leader)    │  │ (Follower)  │  │   (Follower)    │    │
│  │             │  │             │  │                 │    │
│  │ Consul      │  │ Consul      │  │ Consul          │    │
│  │ Nomad       │  │ Nomad       │  │ Nomad           │    │
│  │ Prometheus  │  │ Prometheus  │  │ Prometheus      │    │
│  │ Grafana     │  │ Grafana     │  │ Grafana         │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Worker Nodes                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │  Worker-1   │  │  Worker-2   │  │   Worker-3+     │    │
│  │             │  │             │  │                 │    │
│  │ ML Training │  │ ML Training │  │ ML Training     │    │
│  │ Jobs        │  │ Jobs        │  │ Jobs            │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### 5-Node Recommended HA Setup
```
Load Balancer: 2 nodes (Active-Passive)
Control Plane: 3 nodes (Consul/Nomad quorum)
Worker Nodes:  3+ nodes (ML workload execution)
Database:      3 nodes (if external database used)
Storage:       3+ nodes (distributed storage)
```

### 2. Component-Specific HA Configuration

#### Consul HA Configuration
```hcl
# consul-ha.hcl
datacenter = "mlops-dc1"
data_dir = "/consul/data"
log_level = "INFO"
server = true

# HA Configuration
bootstrap_expect = 3
retry_join = [
  "consul-1.internal",
  "consul-2.internal", 
  "consul-3.internal"
]

# Network Configuration
bind_addr = "{{ GetInterfaceIP \"eth0\" }}"
client_addr = "0.0.0.0"

# Performance
performance {
  raft_multiplier = 1
}

# Ports
ports {
  grpc = 8502
}

# Connect/Service Mesh
connect {
  enabled = true
}

# UI and API
ui_config {
  enabled = true
}

api_config {
  enable_streaming = true
}

# ACL Configuration (Production)
acl = {
  enabled = true
  default_policy = "deny"
  enable_token_persistence = true
  tokens = {
    initial_management = "bootstrap-token-here"
  }
}

# Encryption
encrypt = "base64-encoded-32-byte-key-here"
encrypt_verify_incoming = true
encrypt_verify_outgoing = true

# TLS Configuration
tls {
  defaults {
    verify_incoming = true
    verify_outgoing = true
    ca_file = "/consul/tls/ca.pem"
    cert_file = "/consul/tls/consul.pem"
    key_file = "/consul/tls/consul-key.pem"
  }
  
  internal_rpc {
    verify_server_hostname = true
  }
}

# Autopilot
autopilot {
  cleanup_dead_servers = true
  last_contact_threshold = "200ms"
  max_trailing_logs = 250
  server_stabilization_time = "10s"
}

# Logging
log_rotate_duration = "24h"
log_rotate_max_files = 30
```

#### Nomad HA Configuration
```hcl
# nomad-ha.hcl
datacenter = "mlops-dc1"
data_dir = "/nomad/data"
log_level = "INFO"

# Server Configuration (Control Plane Nodes)
server {
  enabled = true
  bootstrap_expect = 3
  
  server_join {
    retry_join = [
      "nomad-1.internal:4648",
      "nomad-2.internal:4648",
      "nomad-3.internal:4648"
    ]
    retry_max = 3
    retry_interval = "15s"
  }
  
  # Autopilot
  autopilot {
    cleanup_dead_servers = true
    last_contact_threshold = "200ms"
    max_trailing_logs = 250
    server_stabilization_time = "10s"
  }
  
  # Raft Protocol
  raft_protocol = 3
}

# Client Configuration (Worker Nodes)
client {
  enabled = true
  
  server_join {
    retry_join = [
      "nomad-1.internal:4647",
      "nomad-2.internal:4647", 
      "nomad-3.internal:4647"
    ]
  }
  
  # Resource Configuration
  reserved {
    cpu = 500
    memory = 512
    disk = 1024
  }
  
  # Host Volumes
  host_volume "ml-data" {
    path = "/opt/ml-data"
    read_only = false
  }
}

# Consul Integration
consul {
  address = "localhost:8500"
  server_service_name = "nomad"
  client_service_name = "nomad-client"
  auto_advertise = true
  server_auto_join = true
  client_auto_join = true
}

# TLS Configuration
tls {
  http = true
  rpc = true
  
  ca_file = "/nomad/tls/ca.pem"
  cert_file = "/nomad/tls/nomad.pem"
  key_file = "/nomad/tls/nomad-key.pem"
  
  verify_server_hostname = true
  verify_https_client = true
}

# ACL Configuration
acl {
  enabled = true
  token_ttl = "30s"
  policy_ttl = "60s"
}

# Telemetry
telemetry {
  collection_interval = "10s"
  disable_hostname = false
  prometheus_metrics = true
  publish_allocation_metrics = true
  publish_node_metrics = true
}

# Limits
limits {
  https_handshake_timeout = "5s"
  http_max_conns_per_client = 100
  rpc_handshake_timeout = "5s"
  rpc_max_conns_per_client = 100
}
```

#### Prometheus HA Configuration
```yaml
# prometheus-ha.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'mlops-prod'
    replica: 'prometheus-1'  # Different for each instance

rule_files:
  - "/etc/prometheus/rules/*.yml"

# Alerting
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager-1.internal:9093
          - alertmanager-2.internal:9093
          - alertmanager-3.internal:9093
      timeout: 10s
      api_version: v2

# Service Discovery
scrape_configs:
  # Consul Service Discovery
  - job_name: 'consul-services'
    consul_sd_configs:
      - server: 'consul.service.consul:8500'
        services: []
    
    relabel_configs:
      - source_labels: [__meta_consul_service]
        target_label: job
      - source_labels: [__meta_consul_node]
        target_label: instance

  # Nomad Jobs
  - job_name: 'nomad-jobs'
    consul_sd_configs:
      - server: 'consul.service.consul:8500'
        services: ['nomad-client']
    
    metrics_path: '/v1/metrics'
    params:
      format: ['prometheus']

  # ML Training Jobs
  - job_name: 'ml-training'
    static_configs:
      - targets: ['pushgateway.service.consul:9091']

# Remote Write (for long-term storage)
remote_write:
  - url: "https://prometheus-remote-storage.example.com/api/v1/write"
    remote_timeout: 30s
    queue_config:
      capacity: 10000
      max_samples_per_send: 2000
      batch_send_deadline: 5s
      min_shards: 1
      max_shards: 200

# Storage
storage:
  tsdb:
    path: /prometheus
    retention.time: 15d
    retention.size: 50GB
    wal-compression: true
```

#### Grafana HA Configuration
```yaml
# grafana-ha.yml
[server]
domain = grafana.mlops.internal
http_port = 3000
protocol = https
cert_file = /etc/grafana/tls/grafana.crt
cert_key = /etc/grafana/tls/grafana.key

[database]
type = postgres
host = postgres.service.consul:5432
name = grafana
user = grafana
password = ${GRAFANA_DB_PASSWORD}
ssl_mode = require
max_idle_conn = 25
max_open_conn = 300

[session]
provider = postgres
provider_config = user=grafana password=${GRAFANA_DB_PASSWORD} host=postgres.service.consul port=5432 dbname=grafana sslmode=require

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}
cookie_secure = true
cookie_samesite = strict

[auth.anonymous]
enabled = false

[auth.basic]
enabled = true

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer
default_theme = dark

[alerting]
enabled = true
execute_alerts = true
error_or_timeout = alerting
nodata_or_nullvalues = no_data
concurrent_render_limit = 5

[unified_alerting]
enabled = true
ha_listen_address = "0.0.0.0:9094"
ha_peer_timeout = 15s
ha_gossip_interval = 200ms
ha_push_pull_interval = 60s

[feature_toggles]
enable = ngalert

[log]
mode = console file
level = info
filters = alerting.notifier.slack:debug

[metrics]
enabled = true
basic_auth_username = prometheus
basic_auth_password = ${PROMETHEUS_PASSWORD}
```

### 3. Load Balancer Configuration

#### HAProxy Configuration
```
# haproxy.cfg
global
    daemon
    maxconn 4096
    log stdout local0 info
    
    # TLS Configuration
    ssl-default-bind-ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option dontlognull
    option redispatch
    retries 3

# Statistics
stats enable
stats uri /stats
stats realm HAProxy\ Statistics
stats auth admin:${HAPROXY_STATS_PASSWORD}

# Frontend - HTTPS
frontend https_frontend
    bind *:443 ssl crt /etc/ssl/certs/mlops.pem
    redirect scheme https if !{ ssl_fc }
    
    # ACL Rules
    acl is_consul hdr_beg(host) -i consul.
    acl is_nomad hdr_beg(host) -i nomad.
    acl is_prometheus hdr_beg(host) -i prometheus.
    acl is_grafana hdr_beg(host) -i grafana.
    
    # Backend Selection
    use_backend consul_backend if is_consul
    use_backend nomad_backend if is_nomad  
    use_backend prometheus_backend if is_prometheus
    use_backend grafana_backend if is_grafana

# Backend - Consul
backend consul_backend
    balance roundrobin
    option httpchk GET /v1/status/leader
    http-check expect status 200
    
    server consul-1 consul-1.internal:8500 check inter 5s
    server consul-2 consul-2.internal:8500 check inter 5s
    server consul-3 consul-3.internal:8500 check inter 5s

# Backend - Nomad  
backend nomad_backend
    balance roundrobin
    option httpchk GET /v1/status/leader
    http-check expect status 200
    
    server nomad-1 nomad-1.internal:4646 check inter 5s
    server nomad-2 nomad-2.internal:4646 check inter 5s
    server nomad-3 nomad-3.internal:4646 check inter 5s

# Backend - Prometheus
backend prometheus_backend
    balance roundrobin
    option httpchk GET /-/healthy
    http-check expect status 200
    
    server prometheus-1 prometheus-1.internal:9090 check inter 10s
    server prometheus-2 prometheus-2.internal:9090 check inter 10s backup

# Backend - Grafana
backend grafana_backend
    balance leastconn
    cookie JSESSIONID prefix nocache
    option httpchk GET /api/health
    http-check expect status 200
    
    server grafana-1 grafana-1.internal:3000 check inter 10s cookie g1
    server grafana-2 grafana-2.internal:3000 check inter 10s cookie g2
    server grafana-3 grafana-3.internal:3000 check inter 10s cookie g3
```

### 4. Database HA Configuration

#### PostgreSQL HA (for Grafana)
```yaml
# postgresql-ha.yml
version: '3.8'
services:
  postgres-primary:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: grafana
      POSTGRES_USER: grafana
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_REPLICATION_USER: replica
      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
    volumes:
      - postgres-primary-data:/var/lib/postgresql/data
      - ./postgresql/primary:/docker-entrypoint-initdb.d
    networks:
      - postgres-ha

  postgres-replica1:
    image: postgres:15-alpine
    environment:
      PGUSER: replica
      POSTGRES_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
      POSTGRES_PRIMARY_HOST: postgres-primary
      POSTGRES_PRIMARY_PORT: 5432
    volumes:
      - postgres-replica1-data:/var/lib/postgresql/data
      - ./postgresql/replica:/docker-entrypoint-initdb.d
    networks:
      - postgres-ha
    depends_on:
      - postgres-primary

  postgres-replica2:
    image: postgres:15-alpine
    environment:
      PGUSER: replica  
      POSTGRES_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
      POSTGRES_PRIMARY_HOST: postgres-primary
      POSTGRES_PRIMARY_PORT: 5432
    volumes:
      - postgres-replica2-data:/var/lib/postgresql/data
      - ./postgresql/replica:/docker-entrypoint-initdb.d
    networks:
      - postgres-ha
    depends_on:
      - postgres-primary

  # PgBouncer for connection pooling
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    environment:
      DATABASES_HOST: postgres-primary
      DATABASES_PORT: 5432
      DATABASES_USER: grafana
      DATABASES_PASSWORD: ${POSTGRES_PASSWORD}
      DATABASES_DBNAME: grafana
    ports:
      - "6432:5432"
    networks:
      - postgres-ha
    depends_on:
      - postgres-primary
```

### 5. Monitoring and Alerting

#### Alertmanager HA Configuration
```yaml
# alertmanager-ha.yml
global:
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alerts@mlops.company.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      service: 'ml-training'
    receiver: 'ml-team'

receivers:
- name: 'default'
  email_configs:
  - to: 'devops@company.com'
    subject: '[MLOps] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@company.com'
    subject: '[CRITICAL] MLOps Alert'
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#mlops-alerts'
    title: 'Critical MLOps Alert'

- name: 'ml-team'
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#ml-training'
    title: 'ML Training Alert'

# HA Configuration
cluster:
  listen-address: "0.0.0.0:9094"
  peer-timeout: 15s
  gossip-interval: 200ms
  push-pull-interval: 60s
  settle-timeout: 60s
  peers:
    - alertmanager-1.internal:9094
    - alertmanager-2.internal:9094
    - alertmanager-3.internal:9094
```

### 6. Network Configuration

#### Security Groups / Firewall Rules
```bash
# Control Plane Nodes
# Consul
iptables -A INPUT -p tcp --dport 8300:8302 -s 10.0.0.0/8 -j ACCEPT  # Consul cluster
iptables -A INPUT -p tcp --dport 8500 -s 10.0.0.0/8 -j ACCEPT       # Consul HTTP API
iptables -A INPUT -p tcp --dport 8600 -s 10.0.0.0/8 -j ACCEPT       # Consul DNS

# Nomad  
iptables -A INPUT -p tcp --dport 4646 -s 10.0.0.0/8 -j ACCEPT       # Nomad HTTP API
iptables -A INPUT -p tcp --dport 4647 -s 10.0.0.0/8 -j ACCEPT       # Nomad RPC
iptables -A INPUT -p tcp --dport 4648 -s 10.0.0.0/8 -j ACCEPT       # Nomad Serf

# Prometheus
iptables -A INPUT -p tcp --dport 9090 -s 10.0.0.0/8 -j ACCEPT       # Prometheus HTTP

# Grafana
iptables -A INPUT -p tcp --dport 3000 -s 10.0.0.0/8 -j ACCEPT       # Grafana HTTP

# Load Balancer Access (from internet)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT                       # HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT                        # HTTP (redirect)

# SSH Access
iptables -A INPUT -p tcp --dport 22 -s ADMIN_IP_RANGE -j ACCEPT     # SSH (restricted)

# Default deny
iptables -A INPUT -j DROP
```

### 7. Deployment Strategy

#### Blue-Green Deployment
```yaml
# docker-compose.blue.yml (Current Production)
version: '3.8'
services:
  consul-blue:
    image: hashicorp/consul:1.16
    # ... configuration
    labels:
      - "deployment=blue"
      - "environment=production"

# docker-compose.green.yml (New Version)  
version: '3.8'
services:
  consul-green:
    image: hashicorp/consul:1.17  # New version
    # ... configuration
    labels:
      - "deployment=green"
      - "environment=staging"
```

#### Rolling Updates
```bash
#!/bin/bash
# rolling_update.sh
set -e

SERVICES=("consul" "nomad" "prometheus" "grafana")

for service in "${SERVICES[@]}"; do
    echo "Updating $service..."
    
    # Update one node at a time
    for node in 1 2 3; do
        echo "Updating $service on node $node..."
        
        # Drain workloads (for Nomad)
        if [ "$service" = "nomad" ]; then
            docker exec nomad-$node nomad node drain -enable -yes
        fi
        
        # Stop service
        docker-compose stop ${service}-${node}
        
        # Update image
        docker-compose pull ${service}-${node}
        
        # Start service
        docker-compose up -d ${service}-${node}
        
        # Wait for health check
        sleep 30
        
        # Verify service is healthy
        if ! curl -f "http://${service}-${node}.internal:${port}/health"; then
            echo "ERROR: $service-$node failed health check"
            exit 1
        fi
        
        # Re-enable node (for Nomad)
        if [ "$service" = "nomad" ]; then
            docker exec nomad-$node nomad node drain -disable
        fi
        
        echo "$service-$node updated successfully"
    done
    
    echo "$service cluster updated successfully"
done

echo "Rolling update completed"
```

### 8. Disaster Recovery

#### Multi-Region Setup
```
Primary Region (us-east-1):
  - Full MLOps stack
  - Production workloads
  - Real-time replication

Secondary Region (us-west-2):  
  - Standby MLOps stack
  - Backup data
  - Disaster recovery

Tertiary Region (eu-west-1):
  - Cold backups
  - Compliance data retention
```

#### Failover Procedures
```bash
#!/bin/bash
# failover.sh
set -e

PRIMARY_REGION="us-east-1"
SECONDARY_REGION="us-west-2"

echo "Initiating disaster recovery failover..."

# 1. Verify primary region is down
if curl -f "https://mlops.$PRIMARY_REGION.company.com/health"; then
    echo "Primary region appears healthy. Aborting failover."
    exit 1
fi

# 2. Promote secondary region
echo "Promoting secondary region to primary..."

# Update DNS to point to secondary region
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://failover-dns.json

# 3. Start services in secondary region
docker-compose -f docker-compose.dr.yml up -d

# 4. Verify services are healthy
services=("consul" "nomad" "prometheus" "grafana")
for service in "${services[@]}"; do
    if ! curl -f "https://$service.$SECONDARY_REGION.company.com/health"; then
        echo "ERROR: $service failed to start in secondary region"
        exit 1
    fi
done

echo "Failover completed. MLOps infrastructure is now running in $SECONDARY_REGION"
```

### 9. Capacity Planning

#### Resource Requirements
```
Minimum 3-Node Setup:
- CPU: 8 cores per node (24 total)
- Memory: 32GB per node (96GB total)
- Storage: 500GB per node (1.5TB total)
- Network: 10Gbps between nodes

Recommended 5-Node Setup:
- Control Plane: 16 cores, 64GB RAM per node
- Worker Nodes: 32 cores, 128GB RAM per node
- Storage: 2TB NVMe SSD per node
- Network: 25Gbps between nodes
```

#### Auto-Scaling Configuration
```hcl
# nomad-autoscaling.hcl
scaling {
  enabled = true
  
  policy {
    cooldown = "2m"
    
    check "cpu_allocated_percentage" {
      source = "prometheus"
      query = "avg(nomad_client_allocated_cpu{node_class=\"ml-workers\"}) / avg(nomad_client_unallocated_cpu{node_class=\"ml-workers\"}) * 100"
      
      strategy "target-value" {
        target = 70
      }
    }
    
    target "aws-asg" {
      resource "worker-nodes-asg" {
        min     = 3
        max     = 20
        dry_run = false
      }
    }
  }
}
```

This HA architecture provides:
- **99.9%+ uptime** through redundancy
- **Automatic failover** for all components  
- **Load distribution** across multiple nodes
- **Data replication** and backup
- **Monitoring and alerting** for proactive management
- **Scalability** to handle increased workloads
- **Security** through encryption and access controls