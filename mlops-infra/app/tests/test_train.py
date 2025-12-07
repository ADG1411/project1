#!/usr/bin/env python3
"""
Unit tests for ML Training Application
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from http.server import HTTPServer
import threading
import time
import requests

# Import modules to test (adjust imports based on actual structure)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from train import (
    MLTrainer, 
    validate_model_name, 
    validate_training_epochs,
    get_env_int,
    HealthCheckHandler,
    HealthCheckServer
)

class TestValidationFunctions:
    """Test validation functions."""
    
    def test_validate_model_name_valid(self):
        """Test valid model names."""
        valid_names = [
            "test-model",
            "test_model",
            "TestModel123",
            "model1",
            "a-b_c123"
        ]
        
        for name in valid_names:
            result = validate_model_name(name)
            assert result == name
    
    def test_validate_model_name_invalid(self):
        """Test invalid model names."""
        invalid_names = [
            "",  # Empty
            "ab",  # Too short
            "a" * 51,  # Too long
            "model with spaces",  # Spaces
            "model@domain",  # Special characters
            "model.name",  # Dots
        ]
        
        for name in invalid_names:
            with pytest.raises(ValueError):
                validate_model_name(name)
    
    def test_validate_training_epochs_valid(self):
        """Test valid training epochs."""
        valid_epochs = ["1", "10", "100", "1000"]
        expected = [1, 10, 100, 1000]
        
        for epoch_str, expected_val in zip(valid_epochs, expected):
            result = validate_training_epochs(epoch_str)
            assert result == expected_val
    
    def test_validate_training_epochs_invalid(self):
        """Test invalid training epochs."""
        invalid_epochs = [
            "0",  # Too low
            "-1",  # Negative
            "1001",  # Too high
            "abc",  # Not a number
            "10.5",  # Float
            "",  # Empty
        ]
        
        for epoch_str in invalid_epochs:
            with pytest.raises(ValueError):
                validate_training_epochs(epoch_str)
    
    def test_get_env_int_with_defaults(self):
        """Test get_env_int function with defaults."""
        # Test with non-existent env var
        result = get_env_int("NON_EXISTENT_VAR", 42)
        assert result == 42
        
        # Test with min/max constraints
        result = get_env_int("NON_EXISTENT_VAR", 50, min_val=10, max_val=100)
        assert result == 50
        
        # Test min constraint enforcement
        result = get_env_int("NON_EXISTENT_VAR", 5, min_val=10, max_val=100)
        assert result == 10
        
        # Test max constraint enforcement
        result = get_env_int("NON_EXISTENT_VAR", 150, min_val=10, max_val=100)
        assert result == 100
    
    @patch.dict(os.environ, {'TEST_ENV_INT': '25'})
    def test_get_env_int_from_environment(self):
        """Test get_env_int reading from environment."""
        result = get_env_int("TEST_ENV_INT", 42)
        assert result == 25
    
    @patch.dict(os.environ, {'TEST_ENV_INVALID': 'not_a_number'})
    def test_get_env_int_invalid_value(self):
        """Test get_env_int with invalid environment value."""
        result = get_env_int("TEST_ENV_INVALID", 42)
        assert result == 42  # Should fall back to default


class TestMLTrainer:
    """Test MLTrainer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.trainer = MLTrainer(model_name="test-model", epochs=3)
    
    def test_initialization(self):
        """Test MLTrainer initialization."""
        assert self.trainer.model_name == "test-model"
        assert self.trainer.epochs == 3
        assert self.trainer.metrics == []
        assert hasattr(self.trainer, 'registry')
        assert hasattr(self.trainer, 'accuracy_gauge')
        assert hasattr(self.trainer, 'loss_gauge')
    
    def test_generate_training_metrics(self):
        """Test metrics generation."""
        metrics = self.trainer.generate_training_metrics(epoch=1)
        
        # Check required fields
        required_fields = [
            'epoch', 'accuracy', 'loss', 'learning_rate',
            'cpu_usage_percent', 'memory_usage_percent', 
            'gpu_usage_percent', 'timestamp', 'batch_size', 'model_name'
        ]
        
        for field in required_fields:
            assert field in metrics
        
        # Check value ranges
        assert 0 <= metrics['accuracy'] <= 1
        assert metrics['loss'] >= 0
        assert metrics['epoch'] == 1
        assert metrics['model_name'] == "test-model"
        assert metrics['batch_size'] == 32
    
    def test_train_epoch(self):
        """Test single epoch training."""
        with patch.object(self.trainer, 'push_metrics_to_prometheus'):
            metrics = self.trainer.train_epoch(epoch=1)
            
            assert len(self.trainer.metrics) == 1
            assert self.trainer.metrics[0] == metrics
            assert metrics['epoch'] == 1
    
    @patch('train.push_to_gateway')
    def test_push_metrics_to_prometheus_success(self, mock_push):
        """Test successful metrics push."""
        mock_push.return_value = None
        
        metrics = self.trainer.generate_training_metrics(epoch=1)
        self.trainer.push_metrics_to_prometheus(metrics)
        
        # Verify push_to_gateway was called
        assert mock_push.called
    
    @patch('train.push_to_gateway')
    def test_push_metrics_to_prometheus_failure(self, mock_push):
        """Test metrics push with retries on failure."""
        from requests.exceptions import ConnectionError
        mock_push.side_effect = ConnectionError("Connection failed")
        
        metrics = self.trainer.generate_training_metrics(epoch=1)
        
        # Should not raise exception, just log errors
        self.trainer.push_metrics_to_prometheus(metrics)
        
        # Should have retried 3 times
        assert mock_push.call_count == 3
    
    def test_save_metrics(self):
        """Test metrics saving to file."""
        # Add some test metrics
        self.trainer.metrics = [
            {'epoch': 1, 'accuracy': 0.8, 'loss': 0.2},
            {'epoch': 2, 'accuracy': 0.85, 'loss': 0.15}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            self.trainer.save_metrics(filepath)
            
            # Verify file was created and contains correct data
            with open(filepath, 'r') as f:
                saved_metrics = json.load(f)
            
            assert saved_metrics == self.trainer.metrics
        finally:
            os.unlink(filepath)
    
    @patch('train.push_to_gateway')
    def test_run_training_success(self, mock_push):
        """Test complete training run."""
        mock_push.return_value = None
        
        with patch('time.sleep'):  # Speed up test
            results = self.trainer.run_training()
        
        assert results['status'] == 'completed'
        assert results['model_name'] == 'test-model'
        assert results['total_epochs'] == 3
        assert len(self.trainer.metrics) == 3
        assert 'final_accuracy' in results
        assert 'training_time_seconds' in results
    
    def test_run_training_with_exception(self):
        """Test training run with exception."""
        with patch.object(self.trainer, 'train_epoch', side_effect=Exception("Test error")):
            results = self.trainer.run_training()
        
        assert results['status'] == 'failed'
        assert 'error' in results
        assert results['error'] == 'Test error'


class TestHealthCheckServer:
    """Test health check server functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.trainer = MLTrainer(model_name="test-model", epochs=5)
        self.health_server = HealthCheckServer(self.trainer, port=0)  # Use random port
    
    def test_health_check_server_initialization(self):
        """Test health check server initialization."""
        assert self.health_server.trainer == self.trainer
        assert self.health_server.server is None
        assert self.health_server.thread is None
    
    def test_health_check_server_start_stop(self):
        """Test starting and stopping health check server."""
        try:
            self.health_server.start()
            
            # Give it a moment to start
            time.sleep(0.1)
            
            assert self.health_server.server is not None
            assert self.health_server.thread is not None
            assert self.health_server.thread.is_alive()
            
            # Get the actual port
            port = self.health_server.server.server_address[1]
            
            # Test health endpoint
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data['status'] == 'healthy'
            assert health_data['model_name'] == 'test-model'
            
        finally:
            self.health_server.stop()
    
    def test_health_check_404_endpoint(self):
        """Test non-existent endpoint returns 404."""
        try:
            self.health_server.start()
            time.sleep(0.1)
            
            port = self.health_server.server.server_address[1]
            
            response = requests.get(f"http://localhost:{port}/nonexistent", timeout=5)
            assert response.status_code == 404
            
        finally:
            self.health_server.stop()


class TestIntegration:
    """Integration tests."""
    
    @patch('train.push_to_gateway')
    def test_main_function_success(self, mock_push):
        """Test main function with valid configuration."""
        mock_push.return_value = None
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'MODEL_NAME': 'integration-test',
            'TRAINING_EPOCHS': '2',
            'HEALTH_CHECK_PORT': '8888'
        }):
            # Mock main function import and execution
            from train import main
            
            with patch('time.sleep'):  # Speed up test
                result = main()
        
        assert result == 0  # Success exit code
    
    def test_main_function_invalid_config(self):
        """Test main function with invalid configuration."""
        with patch.dict(os.environ, {
            'MODEL_NAME': 'invalid model name with spaces',
            'TRAINING_EPOCHS': '0'
        }):
            from train import main
            result = main()
        
        assert result == 1  # Error exit code
    
    @patch('train.main')
    def test_keyboard_interrupt_handling(self, mock_main):
        """Test KeyboardInterrupt handling."""
        mock_main.side_effect = KeyboardInterrupt()
        
        from train import main
        result = main()
        
        assert result == 130  # SIGINT exit code


if __name__ == '__main__':
    pytest.main([__file__, '-v'])