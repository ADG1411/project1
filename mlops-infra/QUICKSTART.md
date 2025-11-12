# MLOps Infrastructure - Quick Setup Guide

## Deployment Commands

### 1. Initial Setup
```bash
# Navigate to project directory
cd mlops-infra

# Build the ML training container image
docker-compose build ml-trainer

# Start all infrastructure services
docker-compose up -d
```

### 2. Verify Services
```powershell
# Check service status
docker-compose ps

# View service logs
docker-compose logs consul
docker-compose logs nomad
docker-compose logs prometheus
docker-compose logs grafana
```

### 3. Access Web Interfaces
- **Nomad UI**: http://localhost:4646
- **Consul UI**: http://localhost:8500
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/mlopsadmin)

### 4. Deploy ML Training Job
```bash
# Wait for services to be ready (60-90 seconds)
# Then submit a training job
docker exec mlops-nomad nomad job run /nomad/config/mlops.nomad

# Check job status
docker exec mlops-nomad nomad job status ml-training

# View running allocations
docker exec mlops-nomad nomad alloc status

# Submit parameterized job with custom parameters
docker exec mlops-nomad nomad job dispatch -meta MODEL_NAME=experiment-1 -meta TRAINING_EPOCHS=20 ml-training
```

### 5. Access Services
- **Nomad UI**: http://localhost:4646
- **Consul UI**: http://localhost:8500
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/mlopsadmin)
- **Pushgateway**: http://localhost:9091

### 6. Cleanup
```bash
# Stop all services
docker-compose down

# Remove volumes (optional - removes persistent data)
docker-compose down -v
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3000, 4646, 8500, 9090 are available
2. **Docker Socket**: Make sure Docker Desktop is running
3. **Memory**: Ensure at least 4GB RAM is available
4. **Network**: Check Windows Firewall settings for Docker networks

### Health Checks
```bash
# Test Consul
curl http://localhost:8500/v1/status/leader

# Test Nomad
curl http://localhost:4646/v1/status/leader

# Test Prometheus
curl http://localhost:9090/-/healthy

# Test Grafana
curl http://localhost:3000/api/health

# Test Pushgateway
curl http://localhost:9091/-/healthy

# View ML training metrics
curl http://localhost:9091/metrics
```