#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Raydium Protocol - Save Module
Author: ECLIPSEMOON
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any

import aiohttp
from pydantic import BaseModel

# Setup logger
logger = logging.getLogger("raydium.save")


class ConfigData(BaseModel):
    """Model representing configuration data for Raydium protocol."""
    
    default_slippage: Decimal = Decimal("0.005")  # 0.5% default slippage
    auto_claim_rewards: bool = True
    default_fee_tier: str = "0.25%"
    favorite_farms: List[str] = []
    favorite_pools: List[str] = []
    custom_rpc_endpoint: Optional[str] = None
    transaction_timeout: int = 30  # seconds


class StateData(BaseModel):
    """Model representing state data for Raydium protocol."""
    
    last_sync_timestamp: int
    positions: Dict[str, Any]
    stake_positions: Dict[str, Any]
    transaction_history: List[Dict[str, Any]]
    rewards_history: List[Dict[str, Any]]


async def save_config(
    config: Dict[str, Any],
    config_path: Optional[str] = None,
) -> bool:
    """
    Save configuration data for Raydium protocol.
    
    Args:
        config: Configuration data to save
        config_path: Path to save configuration file (if None, use default)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Saving Raydium configuration")
    
    # Validate configuration data
    try:
        config_data = ConfigData(**config)
    except Exception as e:
        logger.error(f"Invalid configuration data: {str(e)}")
        return False
    
    # Determine config path
    if config_path is None:
        config_path = _get_default_config_path()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Save configuration to file
    try:
        with open(config_path, 'w') as f:
            # Convert Decimal objects to strings for JSON serialization
            config_dict = _prepare_for_json(config_data.dict())
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False


async def load_config(
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load configuration data for Raydium protocol.
    
    Args:
        config_path: Path to load configuration file from (if None, use default)
        
    Returns:
        Dict[str, Any]: Configuration data
    """
    logger.info("Loading Raydium configuration")
    
    # Determine config path
    if config_path is None:
        config_path = _get_default_config_path()
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logger.info(f"Configuration file not found at {config_path}, using default configuration")
        return ConfigData().dict()
    
    # Load configuration from file
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert string values back to Decimal where needed
        config_dict = _convert_to_decimal(config_dict, ["default_slippage"])
        
        # Validate configuration data
        config_data = ConfigData(**config_dict)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config_data.dict()
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return ConfigData().dict()


async def save_state(
    state: Dict[str, Any],
    state_path: Optional[str] = None,
) -> bool:
    """
    Save state data for Raydium protocol.
    
    Args:
        state: State data to save
        state_path: Path to save state file (if None, use default)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Saving Raydium state")
    
    # Update last sync timestamp
    state["last_sync_timestamp"] = int(datetime.now().timestamp())
    
    # Validate state data
    try:
        state_data = StateData(**state)
    except Exception as e:
        logger.error(f"Invalid state data: {str(e)}")
        return False
    
    # Determine state path
    if state_path is None:
        state_path = _get_default_state_path()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    # Save state to file
    try:
        with open(state_path, 'w') as f:
            # Convert Decimal objects to strings for JSON serialization
            state_dict = _prepare_for_json(state_data.dict())
            json.dump(state_dict, f, indent=2)
        
        logger.info(f"State saved to {state_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving state: {str(e)}")
        return False


async def load_state(
    state_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load state data for Raydium protocol.
    
    Args:
        state_path: Path to load state file from (if None, use default)
        
    Returns:
        Dict[str, Any]: State data
    """
    logger.info("Loading Raydium state")
    
    # Determine state path
    if state_path is None:
        state_path = _get_default_state_path()
    
    # Check if state file exists
    if not os.path.exists(state_path):
        logger.info(f"State file not found at {state_path}, initializing new state")
        return _initialize_new_state()
    
    # Load state from file
    try:
        with open(state_path, 'r') as f:
            state_dict = json.load(f)
        
        # Convert string values back to Decimal where needed in nested structures
        state_dict = _convert_nested_decimals(state_dict)
        
        # Validate state data
        state_data = StateData(**state_dict)
        
        logger.info(f"State loaded from {state_path}")
        return state_data.dict()
    except Exception as e:
        logger.error(f"Error loading state: {str(e)}")
        return _initialize_new_state()


async def backup_data(
    backup_dir: Optional[str] = None,
) -> bool:
    """
    Create a backup of configuration and state data.
    
    Args:
        backup_dir: Directory to store backup files (if None, use default)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Creating backup of Raydium data")
    
    # Determine backup directory
    if backup_dir is None:
        backup_dir = _get_default_backup_dir()
    
    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create timestamp for backup files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup configuration
    config_path = _get_default_config_path()
    if os.path.exists(config_path):
        backup_config_path = os.path.join(backup_dir, f"raydium_config_{timestamp}.json")
        try:
            with open(config_path, 'r') as src, open(backup_config_path, 'w') as dst:
                dst.write(src.read())
            logger.info(f"Configuration backed up to {backup_config_path}")
        except Exception as e:
            logger.error(f"Error backing up configuration: {str(e)}")
            return False
    
    # Backup state
    state_path = _get_default_state_path()
    if os.path.exists(state_path):
        backup_state_path = os.path.join(backup_dir, f"raydium_state_{timestamp}.json")
        try:
            with open(state_path, 'r') as src, open(backup_state_path, 'w') as dst:
                dst.write(src.read())
            logger.info(f"State backed up to {backup_state_path}")
        except Exception as e:
            logger.error(f"Error backing up state: {str(e)}")
            return False
    
    return True


async def restore_from_backup(
    config_backup_path: Optional[str] = None,
    state_backup_path: Optional[str] = None,
) -> bool:
    """
    Restore configuration and state data from backup files.
    
    Args:
        config_backup_path: Path to configuration backup file (if None, don't restore config)
        state_backup_path: Path to state backup file (if None, don't restore state)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Restoring Raydium data from backup")
    
    success = True
    
    # Restore configuration if path provided
    if config_backup_path:
        if not os.path.exists(config_backup_path):
            logger.error(f"Configuration backup file not found at {config_backup_path}")
            success = False
        else:
            config_path = _get_default_config_path()
            try:
                with open(config_backup_path, 'r') as src, open(config_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"Configuration restored from {config_backup_path}")
            except Exception as e:
                logger.error(f"Error restoring configuration: {str(e)}")
                success = False
    
    # Restore state if path provided
    if state_backup_path:
        if not os.path.exists(state_backup_path):
            logger.error(f"State backup file not found at {state_backup_path}")
            success = False
        else:
            state_path = _get_default_state_path()
            try:
                with open(state_backup_path, 'r') as src, open(state_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"State restored from {state_backup_path}")
            except Exception as e:
                logger.error(f"Error restoring state: {str(e)}")
                success = False
    
    return success


async def list_backups(
    backup_dir: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List available backup files.
    
    Args:
        backup_dir: Directory to look for backup files (if None, use default)
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with lists of config and state backups
    """
    logger.info("Listing Raydium data backups")
    
    # Determine backup directory
    if backup_dir is None:
        backup_dir = _get_default_backup_dir()
    
    # Check if backup directory exists
    if not os.path.exists(backup_dir):
        logger.info(f"Backup directory not found at {backup_dir}")
        return {"config_backups": [], "state_backups": []}
    
    # List backup files
    config_backups = []
    state_backups = []
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if not os.path.isfile(filepath):
            continue
        
        file_stats = os.stat(filepath)
        file_info = {
            "filename": filename,
            "path": filepath,
            "size_bytes": file_stats.st_size,
            "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
        }
        
        if filename.startswith("raydium_config_"):
            config_backups.append(file_info)
        elif filename.startswith("raydium_state_"):
            state_backups.append(file_info)
    
    # Sort backups by creation time (newest first)
    config_backups.sort(key=lambda x: x["created_at"], reverse=True)
    state_backups.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "config_backups": config_backups,
        "state_backups": state_backups
    }


# Helper functions

def _get_default_config_path() -> str:
    """Get default path for configuration file."""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".eclipsemoon", "raydium", "config.json")


def _get_default_state_path() -> str:
    """Get default path for state file."""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".eclipsemoon", "raydium", "state.json")


def _get_default_backup_dir() -> str:
    """Get default directory for backup files."""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".eclipsemoon", "raydium", "backups")


def _initialize_new_state() -> Dict[str, Any]:
    """Initialize a new state data structure."""
    return {
        "last_sync_timestamp": int(datetime.now().timestamp()),
        "positions": {},
        "stake_positions": {},
        "transaction_history": [],
        "rewards_history": []
    }


def _prepare_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for JSON serialization by converting Decimal objects to strings."""
    result = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _prepare_for_json(value)
        elif isinstance(value, list):
            result[key] = [
                _prepare_for_json(item) if isinstance(item, dict) else
                str(item) if isinstance(item, Decimal) else
                item
                for item in value
            ]
        else:
            result[key] = value
    return result


def _convert_to_decimal(data: Dict[str, Any], decimal_keys: List[str]) -> Dict[str, Any]:
    """Convert string values to Decimal for specified keys."""
    result = data.copy()
    for key in decimal_keys:
        if key in result and isinstance(result[key], str):
            try:
                result[key] = Decimal(result[key])
            except:
                pass
    return result


def _convert_nested_decimals(data: Any) -> Any:
    """Recursively convert string values that look like decimals to Decimal objects."""
    if isinstance(data, dict):
        return {k: _convert_nested_decimals(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_convert_nested_decimals(item) for item in data]
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


# Example usage
if __name__ == "__main__":
    async def example():
        # Example: Save configuration
        config = {
            "default_slippage": Decimal("0.01"),  # 1% slippage
            "auto_claim_rewards": True,
            "default_fee_tier": "0.25%",
            "favorite_farms": ["farm_1", "farm_3"],
            "favorite_pools": ["pool_1"],
            "custom_rpc_endpoint": "https://api.mainnet-beta.solana.com",
            "transaction_timeout": 45
        }
        
        save_result = await save_config(config)
        print(f"Save configuration result: {save_result}")
        
        # Example: Load configuration
        loaded_config = await load_config()
        print(f"Loaded configuration: {loaded_config}")
        
        # Example: Initialize and save state
        state = _initialize_new_state()
        state["positions"] = {
            "position_1": {
                "pool_id": "pool_1",
                "token_a_amount": Decimal("10"),
                "token_b_amount": Decimal("1000")
            }
        }
        state["stake_positions"] = {
            "stake_1": {
                "farm_id": "farm_1",
                "amount": Decimal("50")
            }
        }
        
        save_state_result = await save_state(state)
        print(f"Save state result: {save_state_result}")
        
        # Example: Load state
        loaded_state = await load_state()
        print(f"Loaded state: {loaded_state}")
        
        # Example: Create backup
        backup_result = await backup_data()
        print(f"Backup result: {backup_result}")
        
        # Example: List backups
        backups = await list_backups()
        print(f"Available backups: {backups}")
    
    # Run example
    asyncio.run(example())