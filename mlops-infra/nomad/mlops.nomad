job "ml-training" {
  datacenters = ["mlops-dc1"]
  type        = "batch"
  
  # Job metadata
  meta {
    version = "1.0.0"
    owner   = "mlops-team"
    project = "ml-pipeline"
  }

  # Parameterized job configuration
  parameterized {
    meta_keys     = ["MODEL_NAME", "TRAINING_EPOCHS", "EXPERIMENT_ID"]
    meta_required = ["MODEL_NAME"]
    payload       = "optional"
  }

  group "ml-trainer" {
    count = 1

    # Restart policy for batch jobs
    restart {
      attempts = 3
      interval = "5m"
      delay    = "25s"
      mode     = "delay"
    }

    # Resource allocation
    task "training" {
      driver = "docker"

      # Docker configuration
      config {
        image = "mlops-trainer:latest"
        
        # Mount docker socket (if needed for container-in-container operations)
        volumes = [
          "/tmp:/tmp"
        ]
        
        # Network configuration
        network_mode = "mlops-infra_mlops-network"
        
        # Force pull latest image
        force_pull = false
        
        # Logging configuration
        logging {
          type = "json-file"
          config {
            max-file = "3"
            max-size = "10m"
          }
        }
      }

      # Environment variables
      env {
        MODEL_NAME       = "${NOMAD_META_MODEL_NAME}"
        TRAINING_EPOCHS  = "${NOMAD_META_TRAINING_EPOCHS}"
        EXPERIMENT_ID    = "${NOMAD_META_EXPERIMENT_ID}"
        NOMAD_JOB_NAME   = "${NOMAD_JOB_NAME}"
        NOMAD_ALLOC_ID   = "${NOMAD_ALLOC_ID}"
      }

      # Resource requirements
      resources {
        cpu    = 500    # MHz
        memory = 512    # MB
        
        # Network configuration
        network {
          mbits = 10
          
          # Port for health checks (optional)
          port "health" {
            static = 8080
          }
        }
      }

      # Service registration with Consul
      service {
        name = "ml-training"
        port = "health"
        tags = [
          "ml",
          "training",
          "batch",
          "python"
        ]
        
        meta {
          model_name = "${NOMAD_META_MODEL_NAME}"
          job_id     = "${NOMAD_JOB_NAME}"
          alloc_id   = "${NOMAD_ALLOC_ID}"
        }

        # Health check configuration
        check {
          type     = "http"
          name     = "training-health"
          path     = "/health"
          interval = "30s"
          timeout  = "10s"
          
          # Check response contains expected fields
          check_restart {
            limit = 3
            grace = "60s"
            ignore_warnings = false
          }
        }
      }

      # Artifact download (if needed for model files, datasets, etc.)
      # artifact {
      #   source      = "https://example.com/dataset.zip"
      #   destination = "local/data/"
      # }

      # Template for dynamic configuration
      template {
        data = <<EOF
# Training Configuration
MODEL_NAME: {{ env "NOMAD_META_MODEL_NAME" | default "default-model" }}
EPOCHS: {{ env "NOMAD_META_TRAINING_EPOCHS" | default "10" }}
EXPERIMENT: {{ env "NOMAD_META_EXPERIMENT_ID" | default "exp-001" }}
TIMESTAMP: {{ timestamp }}
ALLOCATION: {{ env "NOMAD_ALLOC_ID" }}
EOF
        destination = "local/config.yaml"
      }

      # Parameter validation template
      template {
        data = <<EOF
#!/bin/bash
# Parameter validation script
set -e

MODEL_NAME="{{ env "NOMAD_META_MODEL_NAME" }}"
EPOCHS="{{ env "NOMAD_META_TRAINING_EPOCHS" | default "10" }}"

# Validate MODEL_NAME is provided and alphanumeric
if [[ -z "$MODEL_NAME" ]]; then
    echo "ERROR: MODEL_NAME is required"
    exit 1
fi

if [[ ! "$MODEL_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "ERROR: MODEL_NAME must contain only alphanumeric characters, hyphens, and underscores"
    exit 1
fi

# Validate EPOCHS is a number between 1-1000
if [[ ! "$EPOCHS" =~ ^[0-9]+$ ]] || [[ "$EPOCHS" -lt 1 ]] || [[ "$EPOCHS" -gt 1000 ]]; then
    echo "ERROR: TRAINING_EPOCHS must be a number between 1 and 1000"
    exit 1
fi

echo "Parameter validation passed"
echo "MODEL_NAME: $MODEL_NAME"
echo "TRAINING_EPOCHS: $EPOCHS"
EOF
        destination = "local/validate_params.sh"
        perms = "755"
      }

      # Kill timeout
      kill_timeout = "60s"
    }

    # Ephemeral disk configuration
    ephemeral_disk {
      size = 500  # MB
    }
  }

  # Constraints to ensure proper placement
  constraint {
    attribute = "${attr.kernel.name}"
    value     = "linux"
  }

  # Update strategy
  update {
    max_parallel = 1
    stagger      = "30s"
  }
}