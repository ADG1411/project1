# MLOps Infrastructure - Deployment Checklist

## Pre-Deployment Requirements

### System Requirements
- [ ] Operating System: Windows 10/11, macOS, or Linux
- [ ] RAM: Minimum 4GB available for containers
- [ ] Storage: At least 5GB free disk space
- [ ] CPU: 2+ cores recommended for optimal performance

### Software Dependencies
- [ ] Docker Desktop 4.0+ installed and running
- [ ] Docker Compose v2.0+ available
- [ ] Git installed for cloning repository
- [ ] PowerShell/Terminal access
- [ ] Internet connection for downloading container images

### Network Prerequisites
- [ ] Ports 3000, 4646, 8500, 9090 available (not in use)
- [ ] Windows Firewall configured to allow Docker
- [ ] Corporate firewall allows Docker registry access

## Deployment Steps

### Phase 1: Infrastructure Setup
- [ ] Clone repository to local machine
- [ ] Navigate to `mlops-infra` directory
- [ ] Review `docker-compose.yml` configuration
- [ ] Verify all configuration files present

### Phase 2: Service Deployment
- [ ] Build ML training Docker image: `docker-compose build ml-trainer`
- [ ] Start infrastructure services: `docker-compose up -d`
- [ ] Wait for all services to initialize (60-90 seconds)
- [ ] Verify container status: `docker-compose ps`

### Phase 3: Service Validation
- [ ] Consul UI accessible: http://localhost:8500
- [ ] Nomad UI accessible: http://localhost:4646
- [ ] Prometheus UI accessible: http://localhost:9090
- [ ] Grafana UI accessible: http://localhost:3000

### Phase 4: Integration Testing
- [ ] Consul shows all registered services
- [ ] Nomad displays active nodes and ready status
- [ ] Prometheus shows all targets as "UP"
- [ ] Grafana dashboard displays real-time metrics

### Phase 5: ML Job Testing
- [ ] Submit test ML job via Nomad UI or CLI
- [ ] Verify job appears in Nomad allocations
- [ ] Confirm service registration in Consul
- [ ] Observe metrics updates in Grafana dashboard

## Post-Deployment Verification

### Health Checks
```powershell
# Service connectivity
curl http://localhost:8500/v1/status/leader    # Consul
curl http://localhost:4646/v1/status/leader    # Nomad
curl http://localhost:9090/-/healthy           # Prometheus
curl http://localhost:3000/api/health          # Grafana

# Container status
docker-compose ps
docker-compose logs --tail=50 consul
docker-compose logs --tail=50 nomad
```

### Performance Validation
- [ ] CPU usage < 50% under normal load
- [ ] Memory consumption within expected ranges
- [ ] Network communication between services functional
- [ ] Disk I/O performance adequate for log collection

### Security Verification
- [ ] Containers running with non-root users where possible
- [ ] Network isolation between external and internal services
- [ ] No sensitive data exposed in logs or configurations
- [ ] Default passwords changed (Grafana: admin/mlopsadmin)

## Troubleshooting Guide

### Common Issues
1. **Port Conflicts**: Check if other applications use required ports
2. **Docker Issues**: Restart Docker Desktop and retry
3. **Memory Errors**: Increase Docker memory allocation
4. **Network Problems**: Verify Windows Firewall settings

### Debug Commands
```powershell
# Container inspection
docker inspect mlops-consul
docker inspect mlops-nomad
docker inspect mlops-prometheus
docker inspect mlops-grafana

# Network debugging
docker network ls
docker network inspect mlops-infra_mlops-network

# Log analysis
docker-compose logs -f consul
docker-compose logs -f nomad
```

## Success Criteria

### Functional Requirements
- [ ] All services start without errors
- [ ] Service discovery working between components
- [ ] ML jobs can be submitted and executed successfully
- [ ] Metrics collection functioning across all services
- [ ] Dashboards display real-time data

### Performance Requirements
- [ ] Job submission response time < 5 seconds
- [ ] Metrics collection latency < 30 seconds
- [ ] Dashboard refresh rate ≤ 30 seconds
- [ ] System resource usage within acceptable limits

### Reliability Requirements
- [ ] Services recover automatically after container restart
- [ ] Data persistence maintained across restarts
- [ ] Health checks functioning properly
- [ ] Error handling graceful for failed jobs

## Rollback Procedure

If deployment fails:
```powershell
# Stop all services
docker-compose down

# Remove volumes (if corrupted)
docker-compose down -v

# Clean up containers and images (if needed)
docker system prune -f

# Restart deployment process
docker-compose up -d
```

## Next Steps After Deployment

1. **Customize Dashboards**: Modify Grafana panels for specific metrics
2. **Configure Alerts**: Set up Prometheus alerting rules
3. **Scale Testing**: Test with multiple concurrent ML jobs
4. **Security Hardening**: Implement TLS and authentication
5. **Documentation**: Create operational runbooks for your team

---
**Deployment Date**: ___________  
**Deployed By**: ___________  
**Environment**: ___________  
**Status**: ⬜ Success ⬜ Partial ⬜ Failed