# TLS/SSL Configuration Guide

## Overview
This document provides comprehensive TLS/SSL configuration for all MLOps infrastructure components to ensure encrypted communication and secure data transmission.

## Certificate Authority (CA) Setup

### 1. Create Root CA
```bash
#!/bin/bash
# create_ca.sh
set -e

# Create CA directory structure
mkdir -p tls/{ca,consul,nomad,prometheus,grafana}
cd tls/ca

# Generate CA private key
openssl genrsa -out ca-key.pem 4096

# Generate CA certificate
openssl req -new -x509 -days 3650 -key ca-key.pem -sha256 -out ca.pem -subj "/C=US/ST=CA/L=San Francisco/O=MLOps/CN=MLOps Root CA"

# Set permissions
chmod 400 ca-key.pem
chmod 444 ca.pem

echo "Root CA created successfully"
```

### 2. Certificate Generation Script
```bash
#!/bin/bash
# generate_cert.sh
set -e

SERVICE=$1
DOMAINS=$2

if [ -z "$SERVICE" ] || [ -z "$DOMAINS" ]; then
    echo "Usage: $0 <service> <domains>"
    echo "Example: $0 consul consul.service.consul,localhost,127.0.0.1"
    exit 1
fi

cd tls/$SERVICE

# Generate private key
openssl genrsa -out ${SERVICE}-key.pem 4096

# Create certificate signing request
cat > ${SERVICE}.csr.cnf <<EOF
[req]
default_bits = 4096
prompt = no
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=CA
L=San Francisco
O=MLOps
CN=${SERVICE}.service.consul

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
EOF

# Add DNS and IP SANs
IFS=',' read -ra ADDR <<< "$DOMAINS"
counter=1
for domain in "${ADDR[@]}"; do
    if [[ $domain =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "IP.$counter = $domain" >> ${SERVICE}.csr.cnf
    else
        echo "DNS.$counter = $domain" >> ${SERVICE}.csr.cnf
    fi
    ((counter++))
done

# Generate certificate signing request
openssl req -new -key ${SERVICE}-key.pem -out ${SERVICE}.csr -config ${SERVICE}.csr.cnf

# Sign certificate with CA
openssl x509 -req -in ${SERVICE}.csr -CA ../ca/ca.pem -CAkey ../ca/ca-key.pem -CAcreateserial -out ${SERVICE}.pem -days 365 -extensions v3_req -extfile ${SERVICE}.csr.cnf

# Verify certificate
openssl x509 -in ${SERVICE}.pem -text -noout

# Set permissions
chmod 400 ${SERVICE}-key.pem
chmod 444 ${SERVICE}.pem

# Cleanup
rm ${SERVICE}.csr ${SERVICE}.csr.cnf

echo "Certificate for $SERVICE generated successfully"
```

## Component-Specific TLS Configuration

### 1. Consul TLS Configuration

#### Generate Consul Certificates
```bash
# Generate Consul server certificates
./generate_cert.sh consul "consul.service.consul,server.mlops-dc1.consul,localhost,127.0.0.1,consul-1.internal,consul-2.internal,consul-3.internal"

# Generate Consul client certificates  
./generate_cert.sh consul-client "consul-client.service.consul,localhost,127.0.0.1"
```

#### Consul TLS Configuration (consul-tls.hcl)
```hcl
# consul-tls.hcl
datacenter = "mlops-dc1"
data_dir = "/consul/data"
log_level = "INFO"
server = true
bootstrap_expect = 3

# Basic networking
bind_addr = "{{ GetInterfaceIP \"eth0\" }}"
client_addr = "0.0.0.0"

# TLS Configuration
tls {
  defaults {
    verify_incoming = true
    verify_outgoing = true
    
    # CA certificate
    ca_file = "/consul/tls/ca.pem"
    
    # Server certificate and key
    cert_file = "/consul/tls/consul.pem"
    key_file = "/consul/tls/consul-key.pem"
  }
  
  # Internal RPC (server-to-server)
  internal_rpc {
    verify_server_hostname = true
  }
  
  # HTTPS API
  https {
    verify_incoming = false  # Allow clients without certs to API
  }
  
  # gRPC API
  grpc {
    verify_incoming = true
  }
}

# Ports configuration for TLS
ports {
  http = -1          # Disable HTTP
  https = 8501       # Enable HTTPS
  grpc = 8502        # gRPC port  
  grpc_tls = 8503    # gRPC TLS port
}

# Connect (Service Mesh) TLS
connect {
  enabled = true
  
  ca_config {
    provider = "consul"
    
    config {
      private_key = "/consul/tls/connect-ca-key.pem"
      root_cert = "/consul/tls/connect-ca.pem"
      intermediate_cert_ttl = "8760h"  # 1 year
      leaf_cert_ttl = "72h"           # 3 days
    }
  }
}

# Auto-encrypt (automatically distribute certs to clients)
auto_encrypt {
  allow_tls = true
}

# ACL Configuration
acl = {
  enabled = true
  default_policy = "deny"
  enable_token_persistence = true
}

# Encryption
encrypt = "base64-encoded-32-byte-key"
encrypt_verify_incoming = true
encrypt_verify_outgoing = true

# UI Configuration
ui_config {
  enabled = true
}

# Performance
performance {
  raft_multiplier = 1
}
```

### 2. Nomad TLS Configuration

#### Generate Nomad Certificates
```bash
# Generate Nomad server certificates
./generate_cert.sh nomad "server.global.nomad,nomad.service.consul,localhost,127.0.0.1,nomad-1.internal,nomad-2.internal,nomad-3.internal"

# Generate Nomad client certificates
./generate_cert.sh nomad-client "client.global.nomad,localhost,127.0.0.1"
```

#### Nomad TLS Configuration (nomad-tls.hcl)
```hcl
# nomad-tls.hcl
datacenter = "mlops-dc1"
data_dir = "/nomad/data"
log_level = "INFO"

# Server configuration
server {
  enabled = true
  bootstrap_expect = 3
  
  # Server join with TLS
  server_join {
    retry_join = [
      "nomad-1.internal:4648",
      "nomad-2.internal:4648", 
      "nomad-3.internal:4648"
    ]
    retry_max = 3
    retry_interval = "15s"
  }
}

# Client configuration  
client {
  enabled = true
  
  # Client join with TLS
  server_join {
    retry_join = [
      "nomad-1.internal:4647",
      "nomad-2.internal:4647",
      "nomad-3.internal:4647" 
    ]
  }
}

# TLS Configuration
tls {
  http = true
  rpc = true
  
  # CA certificate
  ca_file = "/nomad/tls/ca.pem"
  
  # Server/client certificate and key
  cert_file = "/nomad/tls/nomad.pem"
  key_file = "/nomad/tls/nomad-key.pem"
  
  # Verification settings
  verify_server_hostname = true
  verify_https_client = false      # Allow clients without certs to HTTPS API
  
  # TLS versions
  tls_min_version = "tls12"
  tls_cipher_suites = "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
  
  # Prefer server cipher suites
  tls_prefer_server_cipher_suites = true
}

# Consul integration with TLS
consul {
  address = "consul.service.consul:8501"
  ssl = true
  ca_file = "/consul/tls/ca.pem"
  cert_file = "/consul/tls/consul-client.pem"  
  key_file = "/consul/tls/consul-client-key.pem"
  
  server_service_name = "nomad"
  client_service_name = "nomad-client"
  auto_advertise = true
  server_auto_join = true
  client_auto_join = true
}

# Telemetry
telemetry {
  prometheus_metrics = true
}
```

### 3. Prometheus TLS Configuration

#### Generate Prometheus Certificates
```bash
# Generate Prometheus certificates
./generate_cert.sh prometheus "prometheus.service.consul,localhost,127.0.0.1,prometheus-1.internal,prometheus-2.internal"
```

#### Prometheus TLS Configuration (prometheus-tls.yml)
```yaml
# prometheus-tls.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'mlops-prod'

# TLS Configuration
tls_server_config:
  cert_file: /etc/prometheus/tls/prometheus.pem
  key_file: /etc/prometheus/tls/prometheus-key.pem
  client_ca_file: /etc/prometheus/tls/ca.pem
  client_auth_type: RequireAndVerifyClientCert

# Rule files
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations with TLS
scrape_configs:
  # Consul with TLS
  - job_name: 'consul'
    consul_sd_configs:
      - server: 'consul.service.consul:8501'
        scheme: https
        tls_config:
          ca_file: /etc/consul/tls/ca.pem
          cert_file: /etc/consul/tls/consul-client.pem
          key_file: /etc/consul/tls/consul-client-key.pem
          server_name: consul.service.consul
        services: []
    
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/tls/ca.pem
      insecure_skip_verify: false

  # Nomad with TLS
  - job_name: 'nomad'
    static_configs:
      - targets:
        - 'nomad-1.internal:4646'
        - 'nomad-2.internal:4646'
        - 'nomad-3.internal:4646'
    
    scheme: https
    metrics_path: '/v1/metrics'
    params:
      format: ['prometheus']
    
    tls_config:
      ca_file: /etc/nomad/tls/ca.pem
      cert_file: /etc/nomad/tls/nomad-client.pem
      key_file: /etc/nomad/tls/nomad-client-key.pem
      server_name: server.global.nomad

  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/tls/ca.pem
      cert_file: /etc/prometheus/tls/prometheus.pem  
      key_file: /etc/prometheus/tls/prometheus-key.pem
      server_name: prometheus.service.consul

# Remote write with TLS
remote_write:
  - url: "https://remote-storage.example.com/api/v1/write"
    tls_config:
      ca_file: /etc/prometheus/tls/ca.pem
      cert_file: /etc/prometheus/tls/prometheus.pem
      key_file: /etc/prometheus/tls/prometheus-key.pem
    
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/remote-write-password

# Alertmanager with TLS
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager-1.internal:9093
          - alertmanager-2.internal:9093
      
      scheme: https
      tls_config:
        ca_file: /etc/prometheus/tls/ca.pem
        cert_file: /etc/prometheus/tls/prometheus.pem
        key_file: /etc/prometheus/tls/prometheus-key.pem
```

### 4. Grafana TLS Configuration

#### Generate Grafana Certificates
```bash
# Generate Grafana certificates
./generate_cert.sh grafana "grafana.service.consul,grafana.mlops.internal,localhost,127.0.0.1,grafana-1.internal,grafana-2.internal"
```

#### Grafana TLS Configuration (grafana-tls.ini)
```ini
[server]
protocol = https
http_port = 3000
domain = grafana.mlops.internal
root_url = https://grafana.mlops.internal/

# TLS Configuration
cert_file = /etc/grafana/tls/grafana.pem
cert_key = /etc/grafana/tls/grafana-key.pem

# TLS settings
tls_min_version = "1.2"
tls_ciphers = "ECDHE-ECDSA-AES256-GCM-SHA384,ECDHE-RSA-AES256-GCM-SHA384,ECDHE-ECDSA-CHACHA20-POLY1305,ECDHE-RSA-CHACHA20-POLY1305"

[database]
type = postgres
host = postgres.service.consul:5432
name = grafana
user = grafana
password = ${GRAFANA_DB_PASSWORD}
ssl_mode = require
ca_cert_path = /etc/grafana/tls/ca.pem
client_cert_path = /etc/grafana/tls/grafana.pem
client_key_path = /etc/grafana/tls/grafana-key.pem

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}
cookie_secure = true
cookie_samesite = strict
strict_transport_security = true
strict_transport_security_max_age_seconds = 86400
strict_transport_security_subdomains = true
strict_transport_security_preload = true

# Data source proxy settings
[dataproxy]
timeout = 30
keep_alive_seconds = 30
tls_handshake_timeout_seconds = 10
expect_continue_timeout_seconds = 1
max_conns_per_host = 0
max_idle_conns = 100
max_idle_conns_per_host = 5

[auth.anonymous]
enabled = false

[auth.basic]
enabled = true

[session]
provider = postgres
provider_config = user=grafana password=${GRAFANA_DB_PASSWORD} host=postgres.service.consul port=5432 dbname=grafana sslmode=require
cookie_secure = true
cookie_name = grafana_sess
session_life_time = 86400
```

## Docker Compose TLS Integration

### Updated docker-compose.yml with TLS
```yaml
# docker-compose-tls.yml
version: '3.8'

networks:
  mlops-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  prometheus-data:
  grafana-data:
  consul-data:
  nomad-data:
  tls-certs:

services:
  # TLS Certificate Generator
  tls-setup:
    build:
      context: ./tls
      dockerfile: Dockerfile.tls-setup
    volumes:
      - tls-certs:/tls
      - ./tls:/tls-config
    command: /generate-all-certs.sh
    networks:
      - mlops-network

  # Consul with TLS
  consul:
    image: hashicorp/consul:1.16
    container_name: mlops-consul
    hostname: consul
    depends_on:
      - tls-setup
    networks:
      mlops-network:
        ipv4_address: 172.20.0.10
    ports:
      - "8501:8501"     # HTTPS UI
      - "8600:8600/udp" # DNS
    volumes:
      - consul-data:/consul/data
      - tls-certs:/consul/tls:ro
      - ./consul/consul-tls.hcl:/consul/config/consul.hcl:ro
    command: ["consul", "agent", "-config-file=/consul/config/consul.hcl"]
    environment:
      - CONSUL_BIND_INTERFACE=eth0
    healthcheck:
      test: ["CMD", "consul", "members", "-ca-file=/consul/tls/ca.pem", "-client-cert=/consul/tls/consul.pem", "-client-key=/consul/tls/consul-key.pem"]
      interval: 5s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  # Nomad with TLS
  nomad:
    image: hashicorp/nomad:1.6
    container_name: mlops-nomad
    hostname: nomad
    depends_on:
      consul:
        condition: service_healthy
    networks:
      mlops-network:
        ipv4_address: 172.20.0.20
    ports:
      - "4646:4646"     # HTTPS UI and API
      - "4647:4647"     # RPC (TLS)
      - "4648:4648"     # Serf
    volumes:
      - nomad-data:/nomad/data
      - tls-certs:/nomad/tls:ro
      - ./nomad/nomad-tls.hcl:/nomad/config/nomad.hcl:ro
      - /var/run/docker.sock:/var/run/docker.sock
    command: ["sh", "-c", "sleep 15 && nomad agent -config=/nomad/config/nomad.hcl"]
    environment:
      - NOMAD_ADDR=https://localhost:4646
      - NOMAD_CACERT=/nomad/tls/ca.pem
      - NOMAD_CLIENT_CERT=/nomad/tls/nomad.pem
      - NOMAD_CLIENT_KEY=/nomad/tls/nomad-key.pem
    healthcheck:
      test: ["CMD", "nomad", "status"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # Prometheus with TLS
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: mlops-prometheus
    hostname: prometheus
    depends_on:
      - consul
      - nomad
    networks:
      mlops-network:
        ipv4_address: 172.20.0.30
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus
      - tls-certs:/etc/prometheus/tls:ro
      - ./prometheus/prometheus-tls.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
      - '--web.config.file=/etc/prometheus/web-config.yml'
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "--ca-certificate=/etc/prometheus/tls/ca.pem", "https://localhost:9090/-/healthy"]
      interval: 5s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  # Grafana with TLS
  grafana:
    image: grafana/grafana:10.1.0
    container_name: mlops-grafana
    hostname: grafana
    depends_on:
      prometheus:
        condition: service_healthy
    networks:
      mlops-network:
        ipv4_address: 172.20.0.40
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - tls-certs:/etc/grafana/tls:ro
      - ./grafana/grafana-tls.ini:/etc/grafana/grafana.ini:ro
      - ./grafana/datasources-tls.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider --ca-certificate=/etc/grafana/tls/ca.pem https://localhost:3000/api/health || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

## Web Configuration for TLS

### Prometheus Web Config (web-config.yml)
```yaml
# web-config.yml
tls_server_config:
  cert_file: /etc/prometheus/tls/prometheus.pem
  key_file: /etc/prometheus/tls/prometheus-key.pem
  client_ca_file: /etc/prometheus/tls/ca.pem
  client_auth_type: RequireAndVerifyClientCert

basic_auth_users:
  prometheus: $2b$12$hNf2lSsxfm0.i4a.1kVpSOVyBCfIB51VRjgBUyv6kdnyTlgWj81Ay  # bcrypt hash
```

### Grafana Data Source with TLS
```yaml
# datasources-tls.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: https://prometheus.service.consul:9090
    isDefault: true
    
    # TLS Configuration
    jsonData:
      tlsAuth: true
      tlsAuthWithCACert: true
      tlsSkipVerify: false
      serverName: prometheus.service.consul
    
    secureJsonData:
      tlsCACert: |
        -----BEGIN CERTIFICATE-----
        # CA certificate content
        -----END CERTIFICATE-----
      tlsClientCert: |
        -----BEGIN CERTIFICATE-----  
        # Client certificate content
        -----END CERTIFICATE-----
      tlsClientKey: |
        -----BEGIN PRIVATE KEY-----
        # Client private key content
        -----END PRIVATE KEY-----

  - name: Consul
    type: consul
    access: proxy
    url: https://consul.service.consul:8501
    
    jsonData:
      tlsAuth: true
      tlsAuthWithCACert: true
      tlsSkipVerify: false
      serverName: consul.service.consul
```

## Certificate Management

### Automatic Certificate Renewal
```bash
#!/bin/bash
# renew_certificates.sh
set -e

CERT_DIR="/opt/mlops/tls"
SERVICES=("consul" "nomad" "prometheus" "grafana")
EXPIRY_DAYS=30  # Renew if certificate expires within 30 days

for service in "${SERVICES[@]}"; do
    cert_file="$CERT_DIR/$service/$service.pem"
    
    if [ ! -f "$cert_file" ]; then
        echo "Certificate not found: $cert_file"
        continue
    fi
    
    # Check certificate expiry
    expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ $days_until_expiry -le $EXPIRY_DAYS ]; then
        echo "Certificate for $service expires in $days_until_expiry days. Renewing..."
        
        # Backup old certificate
        cp "$cert_file" "$cert_file.backup.$(date +%Y%m%d)"
        
        # Generate new certificate
        case $service in
            consul)
                ./generate_cert.sh consul "consul.service.consul,server.mlops-dc1.consul,localhost,127.0.0.1"
                ;;
            nomad)
                ./generate_cert.sh nomad "server.global.nomad,nomad.service.consul,localhost,127.0.0.1"
                ;;
            prometheus)
                ./generate_cert.sh prometheus "prometheus.service.consul,localhost,127.0.0.1"
                ;;
            grafana)
                ./generate_cert.sh grafana "grafana.service.consul,grafana.mlops.internal,localhost,127.0.0.1"
                ;;
        esac
        
        # Reload service
        docker-compose restart $service
        
        echo "Certificate for $service renewed successfully"
    else
        echo "Certificate for $service is valid for $days_until_expiry more days"
    fi
done
```

### Certificate Monitoring
```bash
#!/bin/bash
# monitor_certificates.sh
set -e

CERT_DIR="/opt/mlops/tls"
SERVICES=("consul" "nomad" "prometheus" "grafana")
WARNING_DAYS=14
CRITICAL_DAYS=7

for service in "${SERVICES[@]}"; do
    cert_file="$CERT_DIR/$service/$service.pem"
    
    if [ ! -f "$cert_file" ]; then
        echo "CRITICAL: Certificate not found for $service"
        continue
    fi
    
    # Check certificate expiry
    expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ $days_until_expiry -le $CRITICAL_DAYS ]; then
        echo "CRITICAL: Certificate for $service expires in $days_until_expiry days"
        exit 2
    elif [ $days_until_expiry -le $WARNING_DAYS ]; then
        echo "WARNING: Certificate for $service expires in $days_until_expiry days"
        exit 1
    else
        echo "OK: Certificate for $service is valid for $days_until_expiry more days"
    fi
done

echo "All certificates are valid"
```

## Security Best Practices

### 1. Certificate Security
- Use strong private keys (4096-bit RSA or ECDSA P-384)
- Implement proper certificate rotation (90-day maximum lifetime)
- Use Hardware Security Modules (HSM) for CA keys in production
- Implement Certificate Transparency (CT) logging

### 2. TLS Configuration Security
- Enforce TLS 1.2 minimum (TLS 1.3 preferred)
- Use strong cipher suites only
- Enable Perfect Forward Secrecy (PFS)
- Implement HTTP Strict Transport Security (HSTS)

### 3. Operational Security  
- Regular certificate audits
- Automated certificate monitoring and alerting
- Secure certificate storage and access controls
- Certificate revocation procedures

This TLS configuration provides:
- **End-to-end encryption** for all inter-service communication
- **Certificate-based authentication** between services
- **Automated certificate management** and monitoring
- **Security best practices** implementation
- **Production-ready** TLS configurations