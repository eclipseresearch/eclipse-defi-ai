#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Core Configuration Module
Author: ECLIPSEMOON
"""

import os
import json
import logging
import yaml
from typing import Dict, List, Optional, Union, Any, Callable
from decimal import Decimal

# Setup logger
logger = logging.getLogger("core.config")


class ConfigManager:
    """Manager for configuration files."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files (if None, use default)
        """
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".eclipsemoon", "config")
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(
        self,
        config_name: str,
        default_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            default_config: Default configuration to use if file doesn't exist
            
        Returns:
            Dict[str, Any]: Configuration data
        """
        logger.info(f"Loading configuration: {config_name}")
        
        # Check if config is already loaded
        if config_name in self.configs:
            logger.info(f"Configuration {config_name} already loaded")
            return self.configs[config_name]
        
        # Determine file path
        file_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.info(f"Configuration file {file_path} not found, using default configuration")
            
            if default_config is None:
                default_config = {}
            
            self.configs[config_name] = default_config
            return default_config
        
        try:
            # Load configuration from file
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Convert string values to Decimal where needed
            config = self._convert_decimal_strings(config)
            
            self.configs[config_name] = config
            logger.info(f"Configuration {config_name} loaded successfully")
            
            return config
        
        except Exception as e:
            logger.error(f"Error loading configuration {config_name}: {str(e)}")
            
            if default_config is None:
                default_config = {}
            
            self.configs[config_name] = default_config
            return default_config
    
    def save_config(
        self,
        config_name: str,
        config: Dict[str, Any],
    ) -> bool:
        """
        Save a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            config: Configuration data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Saving configuration: {config_name}")
        
        # Update in-memory config
        self.configs[config_name] = config
        
        # Determine file path
        file_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        try:
            # Convert Decimal objects to strings for JSON serialization
            config_to_save = self._prepare_for_json(config)
            
            # Save configuration to file
            with open(file_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            
            logger.info(f"Configuration {config_name} saved successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error saving configuration {config_name}: {str(e)}")
            return False
    
    def get_config(
        self,
        config_name: str,
        default_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get a configuration from memory or load it if not loaded.
        
        Args:
            config_name: Name of the configuration
            default_config: Default configuration to use if not loaded
            
        Returns:
            Dict[str, Any]: Configuration data
        """
        # Check if config is already loaded
        if config_name in self.configs:
            return self.configs[config_name]
        
        # Load config
        return self.load_config(config_name, default_config)
    
    def update_config(
        self,
        config_name: str,
        updates: Dict[str, Any],
        create_if_not_exists: bool = True,
    ) -> bool:
        """
        Update a configuration with new values.
        
        Args:
            config_name: Name of the configuration
            updates: Updates to apply to the configuration
            create_if_not_exists: Whether to create the configuration if it doesn't exist
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Updating configuration: {config_name}")
        
        # Get current config
        config = self.get_config(config_name, {} if create_if_not_exists else None)
        
        if config is None:
            logger.error(f"Configuration {config_name} not found and create_if_not_exists is False")
            return False
        
        # Apply updates
        self._deep_update(config, updates)
        
        # Save updated config
        return self.save_config(config_name, config)
    
    def delete_config(self, config_name: str) -> bool:
        """
        Delete a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Deleting configuration: {config_name}")
        
        # Remove from in-memory configs
        if config_name in self.configs:
            del self.configs[config_name]
        
        # Determine file path
        file_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.info(f"Configuration file {file_path} not found")
            return True
        
        try:
            # Delete file
            os.remove(file_path)
            
            logger.info(f"Configuration {config_name} deleted successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting configuration {config_name}: {str(e)}")
            return False
    
    def list_configs(self) -> List[str]:
        """
        List all available configuration files.
        
        Returns:
            List[str]: List of configuration names
        """
        logger.info("Listing available configurations")
        
        configs = []
        
        # List files in config directory
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".json"):
                configs.append(filename[:-5])  # Remove .json extension
        
        return configs
    
    def import_config(
        self,
        file_path: str,
        config_name: Optional[str] = None,
    ) -> bool:
        """
        Import a configuration from a file.
        
        Args:
            file_path: Path to the file to import
            config_name: Name to use for the imported configuration (if None, use filename)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Importing configuration from {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} not found")
            return False
        
        try:
            # Determine config name
            if config_name is None:
                config_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Load configuration from file
            with open(file_path, 'r') as f:
                if file_path.endswith(".json"):
                    config = json.load(f)
                elif file_path.endswith((".yaml", ".yml")):
                    config = yaml.safe_load(f)
                else:
                    logger.error(f"Unsupported file format: {file_path}")
                    return False
            
            # Convert string values to Decimal where needed
            config = self._convert_decimal_strings(config)
            
            # Save configuration
            self.configs[config_name] = config
            
            # Save to file
            return self.save_config(config_name, config)
        
        except Exception as e:
            logger.error(f"Error importing configuration from {file_path}: {str(e)}")
            return False
    
    def export_config(
        self,
        config_name: str,
        file_path: str,
        format: str = "json",
    ) -> bool:
        """
        Export a configuration to a file.
        
        Args:
            config_name: Name of the configuration to export
            file_path: Path to export the configuration to
            format: Format to export as (json or yaml)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Exporting configuration {config_name} to {file_path}")
        
        # Get configuration
        config = self.get_config(config_name)
        
        if config is None:
            logger.error(f"Configuration {config_name} not found")
            return False
        
        try:
            # Convert Decimal objects to strings for serialization
            config_to_export = self._prepare_for_json(config)
            
            # Export configuration to file
            with open(file_path, 'w') as f:
                if format.lower() == "json":
                    json.dump(config_to_export, f, indent=2)
                elif format.lower() in ("yaml", "yml"):
                    yaml.dump(config_to_export, f, default_flow_style=False)
                else:
                    logger.error(f"Unsupported format: {format}")
                    return False
            
            logger.info(f"Configuration {config_name} exported successfully to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting configuration {config_name} to {file_path}: {str(e)}")
            return False
    
    # Helper methods
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep update a dictionary with another dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _prepare_for_json(self, data: Any) -> Any:
        """Prepare data for JSON serialization by converting Decimal objects to strings."""
        if isinstance(data, dict):
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, Decimal):
            return str(data)
        else:
            return data
    
    def _convert_decimal_strings(self, data: Any) -> Any:
        """Convert string values that look like decimals to Decimal objects."""
        if isinstance(data, dict):
            return {k: self._convert_decimal_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimal_strings(item) for item in data]
        elif isinstance(data, str):
            # Check if string looks like a decimal
            if data.replace('.', '', 1).isdigit() or (data.startswith('-') and data[1:].replace('.', '', 1).isdigit()):
                try:
                    return Decimal(data)
                except:
                    return data
            return data
        else:
            return data


# Singleton instance of ConfigManager
_config_manager = None


def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """
    Get the singleton instance of ConfigManager.
    
    Args:
        config_dir: Directory to store configuration files (if None, use default)
        
    Returns:
        ConfigManager: Singleton instance of ConfigManager
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    
    return _config_manager


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Get config manager
    config_manager = get_config_manager()
    
    # Create a sample configuration
    sample_config = {
        "api": {
            "url": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "user",
            "password": "password",
            "database": "mydb"
        },
        "logging": {
            "level": "INFO",
            "file": "/var/log/myapp.log",
            "max_size": 10485760,  # 10 MB
            "backup_count": 5
        },
        "features": {
            "feature1": True,
            "feature2": False,
            "feature3": {
                "enabled": True,
                "config": {
                    "param1": 10,
                    "param2": "value"
                }
            }
        },
        "limits": {
            "max_connections": 100,
            "rate_limit": Decimal("10.5"),
            "timeout": 60
        }
    }
    
    # Save configuration
    config_manager.save_config("sample", sample_config)
    
    # Load configuration
    loaded_config = config_manager.load_config("sample")
    print("Loaded configuration:", loaded_config)
    
    # Update configuration
    updates = {
        "api": {
            "timeout": 60
        },
        "features": {
            "feature2": True,
            "feature3": {
                "config": {
                    "param1": 20
                }
            }
        }
    }
    
    config_manager.update_config("sample", updates)
    
    # Get updated configuration
    updated_config = config_manager.get_config("sample")
    print("Updated configuration:", updated_config)
    
    # List available configurations
    configs = config_manager.list_configs()
    print("Available configurations:", configs)
    
    # Export configuration to YAML
    config_manager.export_config("sample", "sample_config.yaml", "yaml")
    
    # Import configuration from YAML
    config_manager.import_config("sample_config.yaml", "sample_from_yaml")
    
    # Delete configuration
    config_manager.delete_config("sample_from_yaml")