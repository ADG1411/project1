datacenter = "mlops-dc1"
data_dir = "/consul/data"

# Server configuration
server = true
bootstrap_expect = 1

# Network configuration
bind_addr = "{{ GetInterfaceIP \"eth0\" }}"
client_addr = "0.0.0.0"

# UI configuration
ui_config {
  enabled = true
}

# Connect (service mesh) configuration
connect {
  enabled = true
}

# Ports configuration
ports {
  grpc = 8502
}

# Log configuration
log_level = "INFO"

# Performance settings
performance {
  raft_multiplier = 1
}

# ACL configuration (disabled for demo)
acl = {
  enabled = false
  default_policy = "allow"
}

# Telemetry for Prometheus
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}