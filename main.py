#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Main entry point for the framework
Author: ECLIPSEMOON
"""

import os
import sys
import logging
import argparse
import asyncio
import yaml
import signal
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )

# Set up initial logging
setup_logging()
logger = logging.getLogger("eclipsemoon")

# Import core modules
try:
    from core.config.config_manager import ConfigManager
    from core.security.key_manager import KeyManager
    from core.blockchain.client import BlockchainClient
    from core.data.market_data import MarketDataProvider
    from core.ai.model_manager import ModelManager
    from core.utils.telemetry import Telemetry
    from core.utils.notification import NotificationManager
except ImportError as e:
    logger.error(f"Failed to import core modules: {e}")
    logger.error("Make sure you have installed the package correctly.")
    sys.exit(1)

# Import protocol modules dynamically
PROTOCOLS = ["drift", "jupiter", "kamino", "lulo", "marginfi", "meteora", "raydium"]
protocol_modules = {}

def load_protocol_modules():
    """Dynamically load all protocol modules"""
    for protocol in PROTOCOLS:
        try:
            module = __import__(f"{protocol}", fromlist=["*"])
            protocol_modules[protocol] = module
            logger.info(f"Loaded protocol module: {protocol}")
        except ImportError as e:
            logger.warning(f"Could not load protocol module {protocol}: {e}")

class EclipseMoon:
    """Main class for the ECLIPSEMOON AI Protocol Framework"""
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """Initialize the framework with configuration"""
        self.start_time = datetime.now()
        self.running = True
        self.version = "0.1.0"
        logger.info(f"Initializing ECLIPSEMOON AI Protocol Framework v{self.version} at {self.start_time}")
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Update logging based on config
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_file = self.config.get("logging", {}).get("file_path")
        setup_logging(log_level, log_file)
        
        # Initialize components
        self._initialize_components()
        
        # Protocol handlers
        self.protocol_handlers = {}
        self._initialize_protocol_handlers()
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()
        
        logger.info("ECLIPSEMOON AI Protocol Framework initialized successfully")
    
    def _initialize_components(self):
        """Initialize core components"""
        # Security and key management
        self.key_manager = KeyManager(
            encryption_level=self.config.get("security", {}).get("encryption_level", "high"),
            key_storage_path=self.config.get("security", {}).get("key_storage_path", "~/.eclipsemoon/keys")
        )
        
        # Blockchain client
        self.blockchain_client = BlockchainClient(
            networks=self.config.get("networks", []),
            key_manager=self.key_manager
        )
        
        # Market data provider
        self.market_data = MarketDataProvider(
            data_sources=self.config.get("data_sources", []),
            cache_dir=self.config.get("data", {}).get("cache_dir", "~/.eclipsemoon/cache")
        )
        
        # AI model manager
        self.model_manager = ModelManager(
            model_config=self.config.get("ai", {}),
            data_provider=self.market_data
        )
        
        # Telemetry
        self.telemetry = Telemetry(
            enabled=self.config.get("telemetry", {}).get("enabled", False),
            endpoint=self.config.get("telemetry", {}).get("endpoint", None)
        )
        
        # Notification manager
        self.notification_manager = NotificationManager(
            config=self.config.get("notifications", {})
        )
    
    def _initialize_protocol_handlers(self):
        """Initialize handlers for each supported protocol"""
        enabled_protocols = self.config.get("protocols", {})
        
        for protocol_name, protocol_config in enabled_protocols.items():
            if not protocol_config.get("enabled", False):
                logger.info(f"Protocol {protocol_name} is disabled in config")
                continue
                
            if protocol_name not in protocol_modules:
                logger.warning(f"Protocol {protocol_name} is enabled but module not found")
                continue
                
            try:
                # Initialize the protocol handler
                handler_class = getattr(protocol_modules[protocol_name], "ProtocolHandler")
                handler = handler_class(
                    config=protocol_config,
                    blockchain_client=self.blockchain_client,
                    market_data=self.market_data,
                    model_manager=self.model_manager
                )
                self.protocol_handlers[protocol_name] = handler
                logger.info(f"Initialized handler for protocol: {protocol_name}")
            except (AttributeError, Exception) as e:
                logger.error(f"Failed to initialize handler for protocol {protocol_name}: {e}")
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, initiating shutdown...")
        self.running = False
        self.shutdown()
        sys.exit(0)
    
    async def execute_strategy(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trading or investment strategy across protocols"""
        strategy_name = strategy_config.get("name", "unnamed_strategy")
        logger.info(f"Executing strategy: {strategy_name}")
        
        # Validate strategy configuration
        if not self._validate_strategy(strategy_config):
            logger.error(f"Invalid strategy configuration for {strategy_name}")
            return {"success": False, "error": "Invalid strategy configuration"}
        
        # Get AI predictions if enabled
        predictions = None
        if strategy_config.get("use_ai_predictions", False):
            predictions = await self.model_manager.get_predictions(
                assets=strategy_config.get("assets", []),
                timeframe=strategy_config.get("timeframe", "1h"),
                prediction_horizon=strategy_config.get("prediction_horizon", 24)
            )
            logger.info(f"AI predictions generated for strategy {strategy_name}")
        
        # Execute protocol-specific actions
        results = {}
        for action in strategy_config.get("actions", []):
            protocol_name = action.get("protocol")
            action_type = action.get("type")
            action_params = action.get("params", {})
            
            if protocol_name not in self.protocol_handlers:
                logger.warning(f"Protocol {protocol_name} not available for action {action_type}")
                results[f"{protocol_name}_{action_type}"] = {"success": False, "error": "Protocol not available"}
                continue
            
            try:
                # Enhance action params with AI predictions if available
                if predictions and action.get("use_predictions", True):
                    action_params["predictions"] = predictions
                
                # Execute the action
                protocol_handler = self.protocol_handlers[protocol_name]
                action_method = getattr(protocol_handler, action_type.replace("-", "_"))
                action_result = await action_method(**action_params)
                
                results[f"{protocol_name}_{action_type}"] = action_result
                logger.info(f"Executed {action_type} on {protocol_name}: {action_result.get('status', 'unknown')}")
                
                # Send notification if configured
                if action.get("notify", False) and action_result.get("success", False):
                    self.notification_manager.send_notification(
                        title=f"Strategy {strategy_name}: {action_type} executed",
                        message=f"Successfully executed {action_type} on {protocol_name}",
                        data=action_result
                    )
            except (AttributeError, Exception) as e:
                error_msg = f"Failed to execute {action_type} on {protocol_name}: {str(e)}"
                logger.error(error_msg)
                results[f"{protocol_name}_{action_type}"] = {"success": False, "error": error_msg}
                
                # Send error notification if configured
                if action.get("notify_errors", True):
                    self.notification_manager.send_notification(
                        title=f"Strategy {strategy_name}: Error",
                        message=f"Failed to execute {action_type} on {protocol_name}: {str(e)}",
                        level="error"
                    )
        
        # Aggregate results
        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_count = len(results)
        
        # Send summary notification if configured
        if strategy_config.get("notify_summary", False):
            self.notification_manager.send_notification(
                title=f"Strategy {strategy_name}: Summary",
                message=f"Executed {total_count} actions, {success_count} succeeded, {total_count - success_count} failed",
                data={"success_rate": f"{success_count}/{total_count}"}
            )
        
        return {
            "strategy_name": strategy_name,
            "success": success_count > 0 and success_count == total_count,
            "actions_succeeded": success_count,
            "actions_total": total_count,
            "results": results,
            "execution_time": (datetime.now() - self.start_time).total_seconds()
        }
    
    def _validate_strategy(self, strategy_config: Dict[str, Any]) -> bool:
        """Validate a strategy configuration"""
        required_fields = ["name", "actions"]
        for field in required_fields:
            if field not in strategy_config:
                logger.error(f"Missing required field in strategy config: {field}")
                return False
        
        # Validate actions
        actions = strategy_config.get("actions", [])
        if not actions or not isinstance(actions, list):
            logger.error("Strategy must contain a non-empty list of actions")
            return False
        
        for action in actions:
            if not isinstance(action, dict):
                logger.error("Each action must be a dictionary")
                return False
            
            if "protocol" not in action or "type" not in action:
                logger.error("Each action must specify 'protocol' and 'type'")
                return False
            
            if action.get("protocol") not in self.protocol_handlers:
                logger.warning(f"Protocol {action.get('protocol')} not available")
                # We don't fail validation here, just warn
        
        return True
    
    async def run_backtest(self, strategy_config: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
        """Run a backtest of a strategy over historical data"""
        logger.info(f"Running backtest for strategy {strategy_config.get('name')} from {start_date} to {end_date}")
        
        # Implementation of backtesting logic
        # This would use historical data and simulate strategy execution
        
        return {
            "success": True,
            "message": "Backtest completed",
            "details": "Backtest implementation placeholder"
        }
    
    async def run_strategy_loop(self, strategy_config: Dict[str, Any], interval_seconds: int = 3600) -> None:
        """Run a strategy in a continuous loop with the specified interval"""
        strategy_name = strategy_config.get("name", "unnamed_strategy")
        logger.info(f"Starting strategy loop for {strategy_name} with {interval_seconds}s interval")
        
        while self.running:
            try:
                logger.info(f"Executing strategy {strategy_name}")
                result = await self.execute_strategy(strategy_config)
                
                if result.get("success", False):
                    logger.info(f"Strategy {strategy_name} executed successfully")
                else:
                    logger.warning(f"Strategy {strategy_name} execution had issues: {result.get('actions_succeeded')}/{result.get('actions_total')} actions succeeded")
                
                # Wait for the next interval
                logger.info(f"Waiting {interval_seconds} seconds until next execution of {strategy_name}")
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in strategy loop for {strategy_name}: {e}")
                # Wait a shorter time before retrying after an error
                await asyncio.sleep(min(interval_seconds, 60))
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status across all protocols"""
        portfolio = {}
        
        for protocol_name, handler in self.protocol_handlers.items():
            try:
                protocol_portfolio = handler.get_portfolio()
                portfolio[protocol_name] = protocol_portfolio
            except Exception as e:
                logger.error(f"Failed to get portfolio for {protocol_name}: {e}")
                portfolio[protocol_name] = {"error": str(e)}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio": portfolio
        }
    
    def shutdown(self):
        """Gracefully shutdown the framework"""
        logger.info("Shutting down ECLIPSEMOON AI Protocol Framework")
        
        # Close connections and clean up resources
        for protocol_name, handler in self.protocol_handlers.items():
            try:
                handler.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {protocol_name}: {e}")
        
        self.blockchain_client.close()
        self.market_data.close()
        self.model_manager.unload_models()
        
        # Final telemetry
        if self.telemetry.enabled:
            self.telemetry.send_event("framework_shutdown", {
                "uptime": (datetime.now() - self.start_time).total_seconds()
            })
        
        logger.info("Shutdown complete")


async def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="ECLIPSEMOON AI Protocol Framework")
    parser.add_argument("--config", type=str, default="config/default.yaml", help="Path to configuration file")
    parser.add_argument("--strategy", type=str, help="Path to strategy configuration file")
    parser.add_argument("--backtest", action="store_true", help="Run in backtest mode")
    parser.add_argument("--start-date", type=str, help="Start date for backtest (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date for backtest (YYYY-MM-DD)")
    parser.add_argument("--loop", action="store_true", help="Run strategy in a continuous loop")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds for strategy loop")
    parser.add_argument("--version", action="store_true", help="Show version information")
    
    args = parser.parse_args()
    
    # Show version and exit if requested
    if args.version:
        print("ECLIPSEMOON AI Protocol Framework v0.1.0")
        print("Author: ECLIPSEMOON")
        return 0
    
    # Load protocol modules
    load_protocol_modules()
    
    # Initialize the framework
    eclipse = EclipseMoon(config_path=args.config)
    
    try:
        if args.strategy:
            # Load strategy configuration
            strategy_path = Path(args.strategy)
            if not strategy_path.exists():
                logger.error(f"Strategy file not found: {args.strategy}")
                return 1
                
            with open(strategy_path, 'r') as f:
                strategy_config = yaml.safe_load(f)
            
            if args.backtest:
                # Run backtest
                if not args.start_date or not args.end_date:
                    logger.error("Backtest requires --start-date and --end-date")
                    return 1
                
                result = await eclipse.run_backtest(
                    strategy_config=strategy_config,
                    start_date=args.start_date,
                    end_date=args.end_date
                )
            elif args.loop:
                # Run strategy in a continuous loop
                await eclipse.run_strategy_loop(
                    strategy_config=strategy_config,
                    interval_seconds=args.interval
                )
            else:
                # Execute strategy once
                result = await eclipse.execute_strategy(strategy_config)
            
            # Print results
            if not args.loop:
                print(yaml.dump(result, default_flow_style=False))
        else:
            # Interactive mode or API server could be implemented here
            logger.info("No strategy specified. Use --strategy to specify a strategy configuration file.")
            
            # For now, just show portfolio status
            portfolio = eclipse.get_portfolio_status()
            print(yaml.dump(portfolio, default_flow_style=False))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        return 1
    finally:
        # Ensure proper shutdown
        eclipse.shutdown()
    
    return 0


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

console.log("This is a Node.js representation of the Python code structure. In a real implementation, this would be Python code.");