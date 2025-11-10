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
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLTrainer:
    """Simulates a machine learning training process"""
    
    def __init__(self, model_name: str = "demo-model", epochs: int = 10):
        self.model_name = model_name
        self.epochs = epochs
        self.metrics = []
        self.start_time = datetime.now()
        
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
        
        logger.info(f"Epoch {epoch} completed - Accuracy: {metrics['accuracy']:.4f}, Loss: {metrics['loss']:.4f}")
        return metrics
    
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

def main():
    """Main function to run the ML training simulation"""
    # Get configuration from environment variables
    model_name = os.getenv('MODEL_NAME', 'demo-model')
    epochs = int(os.getenv('TRAINING_EPOCHS', '10'))
    
    # Create trainer instance
    trainer = MLTrainer(model_name=model_name, epochs=epochs)
    
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

if __name__ == "__main__":
    exit(main())