#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for AI Module
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.ai import ModelManager, ModelConfig, PredictionResult, get_model_manager


class TestModelConfig(unittest.TestCase):
    """Test cases for ModelConfig class."""

    def test_model_config_creation(self):
        """Test creating a ModelConfig instance."""
        config = ModelConfig(
            model_id="test_model",
            model_type="price_prediction",
            version="1.0.0",
            input_features=["price", "volume"],
            output_features=["predicted_price"]
        )
        
        self.assertEqual(config.model_id, "test_model")
        self.assertEqual(config.model_type, "price_prediction")
        self.assertEqual(config.version, "1.0.0")
        self.assertEqual(config.input_features, ["price", "volume"])
        self.assertEqual(config.output_features, ["predicted_price"])
        self.assertEqual(config.hyperparameters, {})
        self.assertEqual(config.metadata, {})


class TestPredictionResult(unittest.TestCase):
    """Test cases for PredictionResult class."""

    def test_prediction_result_creation(self):
        """Test creating a PredictionResult instance."""
        result = PredictionResult(
            prediction={"predicted_price": 100.0},
            confidence=0.85,
            execution_time_ms=150.5,
            model_id="test_model",
            timestamp=1620000000
        )
        
        self.assertEqual(result.prediction, {"predicted_price": 100.0})
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.execution_time_ms, 150.5)
        self.assertEqual(result.model_id, "test_model")
        self.assertEqual(result.timestamp, 1620000000)


class TestModelManager(unittest.TestCase):
    """Test cases for ModelManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for models
        self.test_models_dir = os.path.join(os.path.dirname(__file__), 'test_models')
        os.makedirs(self.test_models_dir, exist_ok=True)
        
        # Create model manager
        self.model_manager = ModelManager(self.test_models_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test files
        for filename in os.listdir(self.test_models_dir):
            file_path = os.path.join(self.test_models_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # Remove test directory
        os.rmdir(self.test_models_dir)
    
    @patch('core.ai.ModelManager._load_price_prediction_model')
    def test_load_model(self, mock_load_model):
        """Test loading a model."""
        # Create test model files
        model_id = "test_model"
        model_path = os.path.join(self.test_models_dir, f"{model_id}.model")
        config_path = os.path.join(self.test_models_dir, f"{model_id}.json")
        
        # Create model file
        with open(model_path, 'w') as f:
            f.write("Test model data")
        
        # Create config file
        config = {
            "model_id": model_id,
            "model_type": "price_prediction",
            "version": "1.0.0",
            "input_features": ["price", "volume"],
            "output_features": ["predicted_price"],
            "hyperparameters": {},
            "metadata": {}
        }
        
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Mock the model loading function
        mock_model = {"type": "price_prediction", "weights": [1, 2, 3]}
        mock_load_model.return_value = asyncio.Future()
        mock_load_model.return_value.set_result(mock_model)
        
        # Load model
        result = asyncio.run(self.model_manager.load_model(model_id))
        
        # Verify results
        self.assertTrue(result)
        self.assertIn(model_id, self.model_manager.models)
        self.assertIn(model_id, self.model_manager.configs)
        self.assertEqual(self.model_manager.configs[model_id].model_id, model_id)
        
        # Verify mock was called
        mock_load_model.assert_called_once()
    
    def test_unload_model(self):
        """Test unloading a model."""
        # Add a model to the manager
        model_id = "test_model"
        self.model_manager.models[model_id] = {"test": "model"}
        self.model_manager.configs[model_id] = ModelConfig(
            model_id=model_id,
            model_type="price_prediction",
            version="1.0.0",
            input_features=["price", "volume"],
            output_features=["predicted_price"]
        )
        
        # Unload model
        result = asyncio.run(self.model_manager.unload_model(model_id))
        
        # Verify results
        self.assertTrue(result)
        self.assertNotIn(model_id, self.model_manager.models)
        self.assertNotIn(model_id, self.model_manager.configs)
    
    @patch('core.ai.ModelManager._predict_price')
    def test_predict(self, mock_predict):
        """Test making a prediction."""
        # Add a model to the manager
        model_id = "test_model"
        self.model_manager.models[model_id] = {"test": "model"}
        self.model_manager.configs[model_id] = ModelConfig(
            model_id=model_id,
            model_type="price_prediction",
            version="1.0.0",
            input_features=["current_price", "volume"],
            output_features=["predicted_price"]
        )
        
        # Mock the prediction function
        prediction = {"predicted_price": 105.0}
        confidence = 0.9
        mock_predict.return_value = asyncio.Future()
        mock_predict.return_value.set_result((prediction, confidence))
        
        # Make prediction
        input_data = {"current_price": 100.0, "volume": 1000.0}
        result = asyncio.run(self.model_manager.predict(model_id, input_data))
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result.prediction, prediction)
        self.assertEqual(result.confidence, confidence)
        self.assertEqual(result.model_id, model_id)
        
        # Verify mock was called
        mock_predict.assert_called_once()
    
    def test_get_model_manager(self):
        """Test getting the singleton model manager."""
        # Get model manager
        manager1 = asyncio.run(get_model_manager(self.test_models_dir))
        manager2 = asyncio.run(get_model_manager(self.test_models_dir))
        
        # Verify it's the same instance
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()