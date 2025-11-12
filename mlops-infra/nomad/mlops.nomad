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
    meta_keys = ["MODEL_NAME", "TRAINING_EPOCHS", "EXPERIMENT_ID"]
    payload   = "optional"
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
          type     = "script"
          name     = "training-status"
          command  = "/bin/sh"
          args     = ["-c", "ps aux | grep -v grep | grep python || exit 1"]
          interval = "30s"
          timeout  = "10s"
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