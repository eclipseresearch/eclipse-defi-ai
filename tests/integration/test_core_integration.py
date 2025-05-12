#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Integration Tests for Core Modules
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import asyncio
import tempfile
import shutil
from decimal import Decimal

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.ai import get_model_manager, ModelConfig
from core.blockchain import get_blockchain_client, DEVNET_CONFIG
from core.config import get_config_manager
from core.data import get_data_manager, DataSource, DataQuery
from core.security import get_security_manager
from core.utils import setup_logging, Timer


class TestCoreIntegration(unittest.TestCase):
    """Integration tests for core modules."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Set up subdirectories
        self.models_dir = os.path.join(self.test_dir, "models")
        self.keys_dir = os.path.join(self.test_dir, "keys")
        self.config_dir = os.path.join(self.test_dir, "config")
        self.data_dir = os.path.join(self.test_dir, "data")
        
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.keys_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up logging
        setup_logging(log_level="INFO")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    async def async_test_config_and_security(self):
        """Test integration between config and security modules."""
        # Get managers
        config_manager = get_config_manager(self.config_dir)
        security_manager = get_security_manager(self.keys_dir)
        
        # Generate encryption key
        key_id = "test_key"
        key = security_manager.generate_encryption_key(key_id)
        
        # Create sensitive configuration
        sensitive_config = {
            "api_key": "secret_api_key",
            "password": "secret_password",
            "credentials": {
                "username": "admin",
                "password": "admin_password"
            }
        }
        
        # Encrypt sensitive data
        encrypted_api_key = security_manager.encrypt_data(sensitive_config["api_key"], key_id)
        encrypted_password = security_manager.encrypt_data(sensitive_config["password"], key_id)
        encrypted_admin_password = security_manager.encrypt_data(
            sensitive_config["credentials"]["password"], key_id
        )
        
        # Create config with encrypted data
        config = {
            "api": {
                "url": "https://api.example.com",
                "encrypted_api_key": base64.b64encode(encrypted_api_key).decode('utf-8')
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "user",
                "encrypted_password": base64.b64encode(encrypted_password).decode('utf-8')
            },
            "admin": {
                "username": "admin",
                "encrypted_password": base64.b64encode(encrypted_admin_password).decode('utf-8')
            },
            "encryption_key_id": key_id
        }
        
        # Save config
        config_manager.save_config("secure_config", config)
        
        # Load config
        loaded_config = config_manager.load_config("secure_config")
        
        # Decrypt sensitive data
        decrypted_api_key = security_manager.decrypt_data(
            base64.b64decode(loaded_config["api"]["encrypted_api_key"]),
            loaded_config["encryption_key_id"]
        ).decode('utf-8')
        
        decrypted_password = security_manager.decrypt_data(
            base64.b64decode(loaded_config["database"]["encrypted_password"]),
            loaded_config["encryption_key_id"]
        ).decode('utf-8')
        
        decrypted_admin_password = security_manager.decrypt_data(
            base64.b64decode(loaded_config["admin"]["encrypted_password"]),
            loaded_config["encryption_key_id"]
        ).decode('utf-8')
        
        # Verify decrypted data
        self.assertEqual(decrypted_api_key, sensitive_config["api_key"])
        self.assertEqual(decrypted_password, sensitive_config["password"])
        self.assertEqual(decrypted_admin_password, sensitive_config["credentials"]["password"])
    
    def test_config_and_security(self):
        """Test integration between config and security modules."""
        asyncio.run(self.async_test_config_and_security())
    
    async def async_test_data_and_config(self):
        """Test integration between data and config modules."""
        # Get managers
        config_manager = get_config_manager(self.config_dir)
        data_manager = get_data_manager(self.data_dir)
        
        # Create database configuration
        db_config = {
            "sources": {
                "test_db": {
                    "name": "Test Database",
                    "type": "database",
                    "connection_info": {
                        "type": "sqlite",
                        "path": os.path.join(self.data_dir, "test.db")
                    }
                }
            }
        }
        
        # Save config
        config_manager.save_config("database_config", db_config)
        
        # Load config
        loaded_config = config_manager.load_config("database_config")
        
        # Register data source from config
        source_config = loaded_config["sources"]["test_db"]
        source = DataSource(
            source_id="test_db",
            name=source_config["name"],
            type=source_config["type"],
            connection_info=source_config["connection_info"]
        )
        
        await data_manager.register_source(source)
        
        # Connect to source
        await data_manager.connect("test_db")
        
        # Create a table
        create_table_query = DataQuery(
            query_id="create_table",
            source_id="test_db",
            query_type="sql",
            query_params={
                "query": """
                CREATE TABLE IF NOT EXISTS test (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value REAL
                )
                """
            }
        )
        
        await data_manager.execute_query(create_table_query)
        
        # Insert data
        insert_query = DataQuery(
            query_id="insert_data",
            source_id="test_db",
            query_type="sql",
            query_params={
                "query": "INSERT INTO test (name, value) VALUES (?, ?)",
                "params": ["Test", 123.45]
            }
        )
        
        await data_manager.execute_query(insert_query)
        
        # Query data
        select_query = DataQuery(
            query_id="select_data",
            source_id="test_db",
            query_type="sql",
            query_params={
                "query": "SELECT * FROM test"
            }
        )
        
        result = await data_manager.execute_query(select_query)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["name"], "Test")
        self.assertEqual(result.data[0]["value"], 123.45)
        
        # Close connection
        await data_manager.close_connection("test_db")
    
    def test_data_and_config(self):
        """Test integration between data and config modules."""
        asyncio.run(self.async_test_data_and_config())
    
    async def async_test_ai_and_data(self):
        """Test integration between AI and data modules."""
        # Get managers
        model_manager = await get_model_manager(self.models_dir)
        data_manager = get_data_manager(self.data_dir)
        
        # Create sample price data
        price_data = [
            {"timestamp": 1620000000, "price": 100.0, "volume": 1000.0},
            {"timestamp": 1620001000, "price": 101.5, "volume": 1200.0},
            {"timestamp": 1620002000, "price": 102.0, "volume": 900.0},
            {"timestamp": 1620003000, "price": 101.0, "volume": 1100.0},
            {"timestamp": 1620004000, "price": 103.0, "volume": 1500.0}
        ]
        
        # Save data to CSV
        csv_path = os.path.join(self.data_dir, "price_data.csv")
        await data_manager.save_data(price_data, csv_path, "csv")
        
        # Create model configuration
        model_config = ModelConfig(
            model_id="price_prediction_v1",
            model_type="price_prediction",
            version="1.0.0",
            input_features=["price", "volume"],
            output_features=["predicted_price"],
            hyperparameters={
                "learning_rate": 0.001,
                "hidden_layers": [64, 32]
            },
            metadata={
                "description": "Price prediction model for testing",
                "data_source": csv_path
            }
        )
        
        # Save model configuration
        with open(os.path.join(self.models_dir, f"{model_config.model_id}.json"), 'w') as f:
            import json
            json.dump(model_config.dict(), f, indent=2)
        
        # Create a dummy model file
        with open(os.path.join(self.models_dir, f"{model_config.model_id}.model"), 'w') as f:
            f.write("Dummy model file")
        
        # Load model
        loaded = await model_manager.load_model(model_config.model_id)
        self.assertTrue(loaded)
        
        # Make a prediction
        prediction_result = await model_manager.predict(
            model_id=model_config.model_id,
            input_data={
                "price": 103.0,
                "volume": 1500.0
            }
        )
        
        # Verify prediction
        self.assertIsNotNone(prediction_result)
        self.assertIn("predicted_price", prediction_result.prediction)
        
        # Unload model
        unloaded = await model_manager.unload_model(model_config.model_id)
        self.assertTrue(unloaded)
    
    def test_ai_and_data(self):
        """Test integration between AI and data modules."""
        asyncio.run(self.async_test_ai_and_data())
    
    def test_utils_with_all_modules(self):
        """Test utils module with all other modules."""
        # Test Timer with various operations
        with Timer("Config operation") as timer:
            config_manager = get_config_manager(self.config_dir)
            config_manager.save_config("test", {"key": "value"})
            loaded_config = config_manager.load_config("test")
            self.assertEqual(loaded_config["key"], "value")
        
        # Verify timer
        self.assertGreater(timer.elapsed(), 0)
        
        # Test retry with blockchain operations
        from core.utils import retry
        
        @retry(max_attempts=3, delay=0.1)
        async def connect_to_blockchain():
            client = await get_blockchain_client("devnet")
            return client is not None
        
        # Run with retry
        result = asyncio.run(connect_to_blockchain())
        
        # This might fail if no internet connection, but the retry mechanism should work
        # We're not asserting the result here, just testing the integration


if __name__ == '__main__':
    unittest.main()