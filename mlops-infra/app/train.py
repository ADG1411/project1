#!/usr/bin/env python3
"""
ML Training Simulation Script for MLOps Pipeline
This script simulates a machine learning training process with metrics logging.
"""

import os
import time
import random
import json
import logging
import re
import threading
from datetime import datetime
from typing import Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint"""
    
    def __init__(self, trainer_instance, *args, **kwargs):
        self.trainer = trainer_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for health checks"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "model_name": self.trainer.model_name if self.trainer else "unknown",
                "epochs_completed": len(self.trainer.metrics) if self.trainer and hasattr(self.trainer, 'metrics') else 0,
                "total_epochs": self.trainer.epochs if self.trainer else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

class HealthCheckServer:
    """HTTP health check server for the ML training application"""
    
    def __init__(self, trainer_instance, port=8080):
        self.trainer = trainer_instance
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health check server in a separate thread"""
        try:
            handler = lambda *args, **kwargs: HealthCheckHandler(self.trainer, *args, **kwargs)
            self.server = HTTPServer(('0.0.0.0', self.port), handler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
    
    def stop(self):
        """Stop the health check server"""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                logger.info("Health check server stopped")
            except Exception as e:
                logger.error(f"Error stopping health check server: {e}")

class MLTrainer:
    """Simulates a machine learning training process"""
    
    def __init__(self, model_name: str = "demo-model", epochs: int = 10):
        self.model_name = model_name
        self.epochs = epochs
        self.metrics = []
        self.start_time = datetime.now()
        
        # Model version for tracking
        self.model_version = os.getenv('MODEL_VERSION', '1.0.0')
        
        # Prometheus metrics
        self.registry = CollectorRegistry()
        self.accuracy_gauge = Gauge('ml_training_accuracy', 'Current training accuracy', ['model_name', 'model_version'], registry=self.registry)
        self.loss_gauge = Gauge('ml_training_loss', 'Current training loss', ['model_name', 'model_version'], registry=self.registry)
        self.epoch_counter = Counter('ml_training_epochs_total', 'Total number of epochs completed', ['model_name', 'model_version'], registry=self.registry)
        self.cpu_gauge = Gauge('ml_training_cpu_usage_percent', 'CPU usage during training', ['model_name', 'model_version'], registry=self.registry)
        self.memory_gauge = Gauge('ml_training_memory_usage_percent', 'Memory usage during training', ['model_name', 'model_version'], registry=self.registry)
        self.metrics_failure_counter = Counter('ml_training_metrics_failures_total', 'Total number of metrics push failures', ['model_name', 'model_version'], registry=self.registry)
        self.training_start_time_gauge = Gauge('ml_training_start_timestamp', 'Training start timestamp', ['model_name', 'model_version'], registry=self.registry)
        self.training_end_time_gauge = Gauge('ml_training_end_timestamp', 'Training end timestamp', ['model_name', 'model_version'], registry=self.registry)
        
        self.pushgateway_url = os.getenv('PUSHGATEWAY_URL', 'http://172.20.0.50:9091')
        
    def generate_training_metrics(self, epoch: int) -> Dict:
        """Generate realistic training metrics for the current epoch"""
        # Simulate improving accuracy with some randomness
        base_accuracy = 0.6 + (epoch / self.epochs) * 0.3
        accuracy = min(0.95, base_accuracy + random.uniform(-0.05, 0.05))
        
        # Simulate decreasing loss
        base_loss = 1.0 - (epoch / self.epochs) * 0.7
        loss = max(0.1, base_loss + random.uniform(-0.1, 0.1))
        
        # Simulate resource usage
        cpu_usage = random.uniform(60, 90)
        memory_usage = random.uniform(70, 85)
        gpu_usage = random.uniform(80, 95) if random.random() > 0.3 else 0
        
        return {
            "epoch": epoch,
            "accuracy": round(accuracy, 4),
            "loss": round(loss, 4),
            "learning_rate": 0.001 * (0.9 ** (epoch // 3)),  # Learning rate decay
            "cpu_usage_percent": round(cpu_usage, 2),
            "memory_usage_percent": round(memory_usage, 2),
            "gpu_usage_percent": round(gpu_usage, 2),
            "timestamp": datetime.now().isoformat(),
            "batch_size": 32,
            "model_name": self.model_name
        }
    
    def train_epoch(self, epoch: int) -> Dict:
        """Simulate training for one epoch"""
        logger.info(f"Starting epoch {epoch}/{self.epochs}")
        
        # Simulate training time (1-3 seconds per epoch)
        training_time = random.uniform(1.0, 3.0)
        time.sleep(training_time)
        
        metrics = self.generate_training_metrics(epoch)
        self.metrics.append(metrics)
        
        # Push metrics to Prometheus Pushgateway
        self.push_metrics_to_prometheus(metrics)
        
        logger.info(f"Epoch {epoch} completed - Accuracy: {metrics['accuracy']:.4f}, Loss: {metrics['loss']:.4f}")
        return metrics
    
    def push_metrics_to_prometheus(self, metrics: Dict):
        """Push training metrics to Prometheus Pushgateway with retry logic and exponential backoff"""
        max_retries = 3
        base_delay = 1  # seconds
        timeout = get_env_int('PUSHGATEWAY_TIMEOUT', 10, 1, 60)  # 10s default, 1-60s range
        
        for attempt in range(max_retries):
            try:
                # Update Prometheus metrics with model version labels
                labels = {'model_name': self.model_name, 'model_version': self.model_version}
                
                self.accuracy_gauge.labels(**labels).set(metrics['accuracy'])
                self.loss_gauge.labels(**labels).set(metrics['loss'])
                self.epoch_counter.labels(**labels).inc()
                self.cpu_gauge.labels(**labels).set(metrics['cpu_usage_percent'])
                self.memory_gauge.labels(**labels).set(metrics['memory_usage_percent'])
                
                # Push to gateway with timeout
                push_to_gateway(
                    self.pushgateway_url, 
                    job=f'ml-training-{self.model_name}', 
                    registry=self.registry,
                    timeout=timeout
                )
                
                logger.debug(f"Pushed metrics to Prometheus Pushgateway: {self.pushgateway_url}")
                return  # Success, exit the retry loop
                
            except Timeout as e:
                error_details = {
                    'exception_type': type(e).__name__,
                    'message': str(e),
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'timeout': timeout
                }
                logger.warning(f"Timeout pushing metrics to Prometheus: {json.dumps(error_details)}")
                
            except ConnectionError as e:
                error_details = {
                    'exception_type': type(e).__name__,
                    'message': str(e),
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'pushgateway_url': self.pushgateway_url
                }
                logger.warning(f"Connection error pushing metrics to Prometheus: {json.dumps(error_details)}")
                
            except RequestException as e:
                error_details = {
                    'exception_type': type(e).__name__,
                    'message': str(e),
                    'attempt': attempt + 1,
                    'max_retries': max_retries
                }
                logger.warning(f"Request error pushing metrics to Prometheus: {json.dumps(error_details)}")
                
            except Exception as e:
                error_details = {
                    'exception_type': type(e).__name__,
                    'message': str(e),
                    'attempt': attempt + 1,
                    'max_retries': max_retries
                }
                logger.error(f"Unexpected error pushing metrics to Prometheus: {json.dumps(error_details)}")
            
            # Increment failure counter
            self.metrics_failure_counter.labels(model_name=self.model_name, model_version=self.model_version).inc()
            
            # If not the last attempt, wait with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
        
        logger.error(f"Failed to push metrics to Prometheus after {max_retries} attempts")
    
    def save_metrics(self, filepath: str = "/tmp/training_metrics.json"):
        """Save training metrics to a file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def run_training(self) -> Dict:
        """Run the complete training process"""
        logger.info(f"Starting ML training for model: {self.model_name}")
        logger.info(f"Training configuration: {self.epochs} epochs")
        
        # Set training start timestamp
        start_timestamp = time.time()
        self.training_start_time_gauge.labels(
            model_name=self.model_name, 
            model_version=self.model_version
        ).set(start_timestamp)
        
        try:
            # Training loop
            for epoch in range(1, self.epochs + 1):
                metrics = self.train_epoch(epoch)
                
                # Simulate validation every 3 epochs
                if epoch % 3 == 0:
                    val_accuracy = metrics['accuracy'] * random.uniform(0.95, 1.05)
                    logger.info(f"Validation accuracy: {val_accuracy:.4f}")
            
            # Calculate final results
            final_accuracy = self.metrics[-1]['accuracy']
            total_time = (datetime.now() - self.start_time).total_seconds()
            
            results = {
                "model_name": self.model_name,
                "final_accuracy": final_accuracy,
                "total_epochs": self.epochs,
                "training_time_seconds": round(total_time, 2),
                "status": "completed",
                "best_accuracy": max([m['accuracy'] for m in self.metrics]),
                "final_loss": self.metrics[-1]['loss']
            }
            
            logger.info(f"Training completed successfully!")
            logger.info(f"Final accuracy: {final_accuracy:.4f}")
            logger.info(f"Total training time: {total_time:.2f} seconds")
            
            # Set training end timestamp
            end_timestamp = time.time()
            self.training_end_time_gauge.labels(
                model_name=self.model_name, 
                model_version=self.model_version
            ).set(end_timestamp)
            
            # Save metrics
            self.save_metrics()
            
            return results
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                "model_name": self.model_name,
                "status": "failed",
                "error": str(e),
                "epochs_completed": len(self.metrics)
            }

def get_env_int(env_var: str, default: int, min_val: int = None, max_val: int = None) -> int:
    """Get integer from environment variable with optional min/max validation"""
    try:
        value = int(os.getenv(env_var, str(default)))
    except ValueError:
        logger.warning(f"Invalid value for {env_var}, using default: {default}")
        value = default
    
    if min_val is not None and value < min_val:
        logger.warning(f"{env_var} value {value} is below minimum {min_val}, using minimum")
        value = min_val
    
    if max_val is not None and value > max_val:
        logger.warning(f"{env_var} value {value} is above maximum {max_val}, using maximum")
        value = max_val
    
    return value

def validate_model_name(model_name: str) -> str:
    """Validate that model name contains only alphanumeric characters"""
    if not model_name:
        raise ValueError("MODEL_NAME cannot be empty")
    
    # Check if model name contains only alphanumeric characters (and hyphens/underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', model_name):
        raise ValueError("MODEL_NAME must contain only alphanumeric characters, hyphens, and underscores")
    
    if len(model_name) < 3:
        raise ValueError("MODEL_NAME must be at least 3 characters long")
    
    if len(model_name) > 50:
        raise ValueError("MODEL_NAME must be no more than 50 characters long")
    
    return model_name

def validate_training_epochs(epochs_str: str) -> int:
    """Validate that training epochs is within the acceptable range (1-1000)"""
    try:
        epochs = int(epochs_str)
    except ValueError:
        raise ValueError("TRAINING_EPOCHS must be a valid integer")
    
    if epochs < 1:
        raise ValueError("TRAINING_EPOCHS must be at least 1")
    
    if epochs > 1000:
        raise ValueError("TRAINING_EPOCHS must be no more than 1000")
    
    return epochs

def main():
    """Main function to run the ML training simulation"""
    health_server = None
    
    try:
        # Get and validate configuration from environment variables
        model_name_raw = os.getenv('MODEL_NAME', 'demo-model')
        epochs_raw = os.getenv('TRAINING_EPOCHS', '10')
        health_port = get_env_int('HEALTH_CHECK_PORT', 8080, 1024, 65535)
        
        # Validate inputs
        model_name = validate_model_name(model_name_raw)
        epochs = validate_training_epochs(epochs_raw)
        
        logger.info(f"Validated configuration - Model: {model_name}, Epochs: {epochs}")
        
        # Create trainer instance
        trainer = MLTrainer(model_name=model_name, epochs=epochs)
        
        # Start health check server
        health_server = HealthCheckServer(trainer, port=health_port)
        health_server.start()
        
        # Run training
        results = trainer.run_training()
        
        # Print final results
        print("\n" + "="*50)
        print("TRAINING RESULTS")
        print("="*50)
        for key, value in results.items():
            print(f"{key.upper()}: {value}")
        print("="*50)
        
        # Return appropriate exit code
        return 0 if results.get('status') == 'completed' else 1
        
    except ValueError as e:
        error_details = {
            'exception_type': type(e).__name__,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"Configuration validation error: {json.dumps(error_details)}")
        print(f"\nConfiguration Error: {e}")
        return 1
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user (Ctrl+C)")
        print("\nTraining interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        error_details = {
            'exception_type': type(e).__name__,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"Unexpected error in main: {json.dumps(error_details)}")
        print(f"\nUnexpected error: {e}")
        return 1
        
    finally:
        # Ensure health server is stopped
        if health_server:
            try:
                health_server.stop()
            except Exception as e:
                logger.error(f"Error stopping health server: {e}")

if __name__ == "__main__":
    exit(main())