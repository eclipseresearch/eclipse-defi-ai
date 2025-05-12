#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for Config Module
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from decimal import Decimal

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.config import ConfigManager, get_config_manager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for configs
        self.test_config_dir = tempfile.mkdtemp()
        
        # Create config manager
        self.config_manager = ConfigManager(self.test_config_dir)
        
        # Sample config
        self.sample_config = {
            "api": {
                "url": "https://api.example.com",
                "timeout": 30
            },
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "limits": {
                "max_connections": 100,
                "rate_limit": Decimal("10.5")
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        shutil.rmtree(self.test_config_dir)
    
    def test_save_and_load_config(self):
        """Test saving and loading a configuration."""
        # Save config
        result = self.config_manager.save_config("test", self.sample_config)
        self.assertTrue(result)
        
        # Check if file was created
        config_path = os.path.join(self.test_config_dir, "test.json")
        self.assertTrue(os.path.exists(config_path))
        
        # Load config
        loaded_config = self.config_manager.load_config("test")
        
        # Verify loaded config
        self.assertEqual(loaded_config["api"]["url"], self.sample_config["api"]["url"])
        self.assertEqual(loaded_config["api"]["timeout"], self.sample_config["api"]["timeout"])
        self.assertEqual(loaded_config["database"]["host"], self.sample_config["database"]["host"])
        self.assertEqual(loaded_config["database"]["port"], self.sample_config["database"]["port"])
        self.assertEqual(loaded_config["limits"]["max_connections"], self.sample_config["limits"]["max_connections"])
        self.assertEqual(loaded_config["limits"]["rate_limit"], self.sample_config["limits"]["rate_limit"])
    
    def test_get_config(self):
        """Test getting a configuration."""
        # Save config
        self.config_manager.save_config("test", self.sample_config)
        
        # Get config
        config = self.config_manager.get_config("test")
        
        # Verify config
        self.assertEqual(config["api"]["url"], self.sample_config["api"]["url"])
        
        # Get non-existent config with default
        default_config = {"default": True}
        config = self.config_manager.get_config("non_existent", default_config)
        
        # Verify default config was returned
        self.assertTrue(config["default"])
    
    def test_update_config(self):
        """Test updating a configuration."""
        # Save config
        self.config_manager.save_config("test", self.sample_config)
        
        # Update config
        updates = {
            "api": {
                "timeout": 60
            },
            "database": {
                "username": "user",
                "password": "password"
            }
        }
        
        result = self.config_manager.update_config("test", updates)
        self.assertTrue(result)
        
        # Get updated config
        config = self.config_manager.get_config("test")
        
        # Verify updates were applied
        self.assertEqual(config["api"]["url"], self.sample_config["api"]["url"])  # Unchanged
        self.assertEqual(config["api"]["timeout"], 60)  # Updated
        self.assertEqual(config["database"]["host"], self.sample_config["database"]["host"])  # Unchanged
        self.assertEqual(config["database"]["port"], self.sample_config["database"]["port"])  # Unchanged
        self.assertEqual(config["database"]["username"], "user")  # Added
        self.assertEqual(config["database"]["password"], "password")  # Added
    
    def test_delete_config(self):
        """Test deleting a configuration."""
        # Save config
        self.config_manager.save_config("test", self.sample_config)
        
        # Delete config
        result = self.config_manager.delete_config("test")
        self.assertTrue(result)
        
        # Check if file was deleted
        config_path = os.path.join(self.test_config_dir, "test.json")
        self.assertFalse(os.path.exists(config_path))
        
        # Verify config was removed from memory
        self.assertNotIn("test", self.config_manager.configs)
    
    def test_list_configs(self):
        """Test listing configurations."""
        # Save multiple configs
        self.config_manager.save_config("test1", self.sample_config)
        self.config_manager.save_config("test2", self.sample_config)
        self.config_manager.save_config("test3", self.sample_config)
        
        # List configs
        configs = self.config_manager.list_configs()
        
        # Verify configs
        self.assertIn("test1", configs)
        self.assertIn("test2", configs)
        self.assertIn("test3", configs)
    
    def test_import_export_config(self):
        """Test importing and exporting a configuration."""
        # Create a temporary file for export/import
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export config
            self.config_manager.save_config("test", self.sample_config)
            result = self.config_manager.export_config("test", temp_path)
            self.assertTrue(result)
            
            # Verify exported file
            with open(temp_path, 'r') as f:
                exported_config = json.load(f)
            
            self.assertEqual(exported_config["api"]["url"], self.sample_config["api"]["url"])
            
            # Import config
            result = self.config_manager.import_config(temp_path, "imported")
            self.assertTrue(result)
            
            # Verify imported config
            imported_config = self.config_manager.get_config("imported")
            self.assertEqual(imported_config["api"]["url"], self.sample_config["api"]["url"])
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_config_manager(self):
        """Test getting the singleton config manager."""
        # Get config manager
        manager1 = get_config_manager(self.test_config_dir)
        manager2 = get_config_manager(self.test_config_dir)
        
        # Verify it's the same instance
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()