# MLOps Infrastructure Platform

[![Build Status](https://github.com/ADG1411/project1/workflows/MLOps%20Infrastructure%20Validation/badge.svg)](https://github.com/ADG1411/project1/actions)
[![Security Scan](https://img.shields.io/badge/security-scanned-green.svg)](https://github.com/ADG1411/project1/security)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A production-ready MLOps infrastructure platform built with HashiCorp Consul, Nomad, Prometheus, and Grafana for scalable machine learning operations.

## 🚀 Features

- **Service Discovery**: Consul-based service mesh with health checks
- **Workload Orchestration**: Nomad for container and job scheduling
- **Monitoring & Metrics**: Prometheus + Grafana observability stack
- **High Availability**: Multi-node cluster support with automatic failover
- **Security**: TLS/SSL encryption, ACL-based access control
- **Scalability**: Auto-scaling ML workloads with resource management
- **CI/CD Integration**: Automated testing and deployment pipelines

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Security](#-security)
- [Monitoring](#-monitoring)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🏃 Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose v2.0+
- 8GB+ RAM and 20GB+ disk space
- Linux/macOS/Windows with WSL2

### One-Command Setup

```bash
# Clone and start the infrastructure
git clone https://github.com/ADG1411/project1.git
cd project1/mlops-infra
cp .env.example .env
docker-compose up -d

# Wait for services to initialize (60-90 seconds)
docker-compose ps

# Access the services
open http://localhost:8500  # Consul UI
open http://localhost:4646  # Nomad UI  
open http://localhost:9090  # Prometheus UI
open http://localhost:3000  # Grafana UI (admin/[see .env file])
```

## 🔒 Security Hardening

### Network Security
- Implement firewall rules restricting access to internal ports
- Use TLS encryption for all inter-service communication
- Network segmentation between public and private services
- VPN or bastion host access for administrative functions

### Access Control
- Enable ACLs in Consul and Nomad with least privilege
- Multi-factor authentication for administrative accounts
- Regular access reviews and permission audits
- Role-based access control (RBAC) implementation

### Container Security
- Use non-root users in container execution
- Implement read-only filesystems where possible
- Regular vulnerability scanning with automated remediation
- Minimal base images with only required dependencies

### Data Protection
- Encrypt data at rest and in transit
- Secure secrets management with rotation policies
- Regular automated backups with tested restore procedures
- Compliance with data protection regulations (GDPR, HIPAA)

## 📚 Complete Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [High Availability Setup](./HA_ARCHITECTURE.md)  
- [TLS/SSL Configuration](./TLS_SSL_CONFIG.md)
- [Backup Procedures](./BACKUP_PROCEDURES.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)

## 🆘 Support & Contributing

For detailed documentation, troubleshooting guides, and contribution guidelines, please refer to the comprehensive documentation in this repository.