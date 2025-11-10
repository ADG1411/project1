# MLOps Infrastructure Architecture

## System Components Diagram

```
                            ┌─── MLOps Infrastructure Stack ───┐
                            │                                   │
┌──────────────────┐        │   ┌─────────────────────────┐     │
│   External       │        │   │      Grafana UI         │     │
│   ML Scientists  │◄───────┼───┤   (Dashboards & Alerts) │     │
│   & Operators    │        │   │      Port: 3000         │     │
└──────────────────┘        │   └─────────────┬───────────┘     │
                            │                 │                 │
                            │   ┌─────────────▼───────────┐     │
                            │   │      Prometheus         │     │
                            │   │   (Metrics Collection)  │     │
                            │   │      Port: 9090         │     │
                            │   └─────────────┬───────────┘     │
                            │                 │                 │
            ┌───────────────┼─────────────────┼─────────────────┼──────────────┐
            │               │                 │                 │              │
            ▼               │   ┌─────────────▼───────────┐     │              ▼
┌──────────────────┐        │   │        Consul           │     │  ┌──────────────────┐
│      Nomad       │◄───────┼───┤   (Service Discovery)  │     │  │      Docker      │
│  (Orchestrator)  │        │   │      Port: 8500        │     │  │    (Runtime)     │
│   Port: 4646     │        │   └─────────────┬───────────┘     │  │                  │
└─────────┬────────┘        │                 │                 │  └─────────┬────────┘
          │                 │                 │                 │            │
          ▼                 │   ┌─────────────▼───────────┐     │            ▼
┌──────────────────┐        │   │    Service Registry     │     │  ┌──────────────────┐
│   Job Scheduler  │        │   │   & Health Checks       │     │  │   ML Training    │
│   & Resource     │        │   │                         │     │  │   Containers     │
│   Manager        │        │   └─────────────────────────┘     │  │   (Dynamic)      │
└──────────────────┘        │                                   │  └──────────────────┘
                            └───────────────────────────────────┘
```

## Network Architecture

```
Docker Network: mlops-network (172.20.0.0/16)
├── Consul:     172.20.0.10:8500
├── Nomad:      172.20.0.20:4646
├── Prometheus: 172.20.0.30:9090
├── Grafana:    172.20.0.40:3000
└── ML Apps:    Dynamic IP assignment
```

## Data Flow

1. **Job Submission**: Users submit ML jobs to Nomad via UI/API
2. **Orchestration**: Nomad schedules containers using Docker driver
3. **Service Discovery**: Consul registers services and monitors health
4. **Metrics Collection**: Prometheus scrapes metrics from all services
5. **Visualization**: Grafana displays real-time dashboards and alerts
6. **Feedback Loop**: Monitoring data informs scaling and optimization decisions

## Component Interactions

### Nomad ↔ Consul
- Automatic service registration for all Nomad jobs
- Health check propagation from tasks to Consul
- Service discovery for inter-job communication

### Prometheus ↔ Services
- Metrics scraping from /metrics endpoints
- Service discovery via Consul integration
- Time-series storage for historical analysis

### Grafana ↔ Prometheus
- Real-time queries for dashboard updates
- Alert rule evaluation and notification
- Historical data analysis and reporting

## Security Considerations

- Network isolation using Docker bridge networks
- Container-level security with non-root users
- Service-to-service communication via internal IPs
- Future: TLS encryption and ACL-based access control