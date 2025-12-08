datacenter = "mlops-dc1"
data_dir = "/nomad/data"

bind_addr = "0.0.0.0"

# Server configuration for single-node setup
server {
  enabled          = true
  bootstrap_expect = 1
}

# Client configuration
client {
  enabled = true
  
  # Docker driver configuration
  host_volume "docker-sock" {
    path      = "/var/run/docker.sock"
    read_only = false
  }
}

# Consul integration
consul {
  address             = "consul:8500"
  server_service_name = "nomad-server"
  client_service_name = "nomad-client"
  auto_advertise      = true
  server_auto_join    = true
  client_auto_join    = true
}

# Enable UI
ui_config {
  enabled = true
}

# Telemetry for Prometheus
telemetry {
  collection_interval = "1s"
  disable_hostname    = true
  prometheus_metrics  = true
  publish_allocation_metrics = true
  publish_node_metrics = true
}

# Ports configuration
ports {
  http = 4646
  rpc  = 4647
  serf = 4648
}

# Plugin configuration for Docker
plugin "docker" {
  config {
    allow_privileged = true
    volumes {
      enabled = true
    }
    endpoint = "unix:///var/run/docker.sock"
  }
}

# ACL configuration (disabled for demo)
acl = {
  enabled = false
}

# Log configuration
log_level = "INFO"
log_json  = false