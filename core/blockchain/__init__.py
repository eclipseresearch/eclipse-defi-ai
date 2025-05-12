#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Core Blockchain Module
Author: ECLIPSEMOON
"""

import asyncio
import logging
import base64
import json
import time
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

import aiohttp
from pydantic import BaseModel

# Setup logger
logger = logging.getLogger("core.blockchain")


class NetworkConfig(BaseModel):
    """Model representing configuration for a blockchain network."""
    
    network_id: str
    name: str
    rpc_url: str
    explorer_url: str
    is_mainnet: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1


class TransactionConfig(BaseModel):
    """Model representing configuration for a transaction."""
    
    max_fee: Optional[Decimal] = None
    priority_fee: Optional[Decimal] = None
    timeout_seconds: int = 60
    skip_preflight: bool = False
    max_retries: int = 3
    retry_delay_seconds: int = 2


class TransactionResult(BaseModel):
    """Model representing the result of a transaction."""
    
    transaction_id: str
    status: str  # confirmed, failed, pending
    block_hash: Optional[str] = None
    block_time: Optional[int] = None
    fee: Optional[Decimal] = None
    error: Optional[str] = None


class BlockchainClient:
    """Client for interacting with blockchain networks."""
    
    def __init__(self, network_config: NetworkConfig):
        """
        Initialize the blockchain client.
        
        Args:
            network_config: Configuration for the blockchain network
        """
        self.network_config = network_config
        self.session = None
    
    async def connect(self) -> bool:
        """
        Connect to the blockchain network.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Connecting to {self.network_config.name} network")
        
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test connection
            response = await self._send_rpc_request("getHealth", [])
            
            if response and response.get("result") == "ok":
                logger.info(f"Connected to {self.network_config.name} network")
                return True
            else:
                logger.error(f"Failed to connect to {self.network_config.name} network")
                return False
        
        except Exception as e:
            logger.error(f"Error connecting to {self.network_config.name} network: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the blockchain network.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Disconnecting from {self.network_config.name} network")
        
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            logger.info(f"Disconnected from {self.network_config.name} network")
            return True
        
        except Exception as e:
            logger.error(f"Error disconnecting from {self.network_config.name} network: {str(e)}")
            return False
    
    async def get_balance(self, address: str, token: Optional[str] = None) -> Optional[Decimal]:
        """
        Get the balance of an address.
        
        Args:
            address: Address to get balance for
            token: Token mint address (if None, get SOL balance)
            
        Returns:
            Optional[Decimal]: Balance if successful, None otherwise
        """
        logger.info(f"Getting balance for address {address}")
        
        try:
            if token:
                # Get token balance
                response = await self._send_rpc_request(
                    "getTokenAccountsByOwner",
                    [
                        address,
                        {"mint": token},
                        {"encoding": "jsonParsed"}
                    ]
                )
                
                if not response or "result" not in response:
                    logger.error(f"Failed to get token balance for address {address}")
                    return None
                
                accounts = response["result"]["value"]
                
                if not accounts:
                    logger.info(f"No token accounts found for address {address} and token {token}")
                    return Decimal("0")
                
                # Sum balances from all accounts
                total_balance = Decimal("0")
                for account in accounts:
                    info = account["account"]["data"]["parsed"]["info"]
                    balance = Decimal(info["tokenAmount"]["amount"]) / (10 ** info["tokenAmount"]["decimals"])
                    total_balance += balance
                
                return total_balance
            
            else:
                # Get SOL balance
                response = await self._send_rpc_request(
                    "getBalance",
                    [address]
                )
                
                if not response or "result" not in response:
                    logger.error(f"Failed to get SOL balance for address {address}")
                    return None
                
                # Convert lamports to SOL
                balance_lamports = Decimal(response["result"]["value"])
                balance_sol = balance_lamports / Decimal("1000000000")  # 1 SOL = 10^9 lamports
                
                return balance_sol
        
        except Exception as e:
            logger.error(f"Error getting balance for address {address}: {str(e)}")
            return None
    
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            Optional[Dict[str, Any]]: Transaction details if successful, None otherwise
        """
        logger.info(f"Getting transaction {transaction_id}")
        
        try:
            response = await self._send_rpc_request(
                "getTransaction",
                [transaction_id, {"encoding": "jsonParsed"}]
            )
            
            if not response or "result" not in response:
                logger.error(f"Failed to get transaction {transaction_id}")
                return None
            
            return response["result"]
        
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
            return None
    
    async def send_transaction(
        self,
        transaction_data: str,
        config: Optional[TransactionConfig] = None,
    ) -> Optional[TransactionResult]:
        """
        Send a transaction to the blockchain.
        
        Args:
            transaction_data: Signed transaction data as base64 string
            config: Transaction configuration (if None, use default)
            
        Returns:
            Optional[TransactionResult]: Transaction result if successful, None otherwise
        """
        logger.info("Sending transaction")
        
        # Use default config if not provided
        if config is None:
            config = TransactionConfig()
        
        try:
            # Send transaction
            response = await self._send_rpc_request(
                "sendTransaction",
                [
                    transaction_data,
                    {
                        "skipPreflight": config.skip_preflight,
                        "maxRetries": config.max_retries
                    }
                ]
            )
            
            if not response or "result" not in response:
                error = response.get("error", {}).get("message", "Unknown error") if response else "No response"
                logger.error(f"Failed to send transaction: {error}")
                
                return TransactionResult(
                    transaction_id="",
                    status="failed",
                    error=error
                )
            
            transaction_id = response["result"]
            
            # Wait for confirmation if timeout is set
            if config.timeout_seconds > 0:
                confirmed = await self._wait_for_confirmation(
                    transaction_id=transaction_id,
                    timeout_seconds=config.timeout_seconds,
                    max_retries=config.max_retries,
                    retry_delay_seconds=config.retry_delay_seconds
                )
                
                if confirmed:
                    # Get transaction details
                    tx_details = await self.get_transaction(transaction_id)
                    
                    if tx_details:
                        return TransactionResult(
                            transaction_id=transaction_id,
                            status="confirmed",
                            block_hash=tx_details.get("blockhash"),
                            block_time=tx_details.get("blockTime"),
                            fee=Decimal(tx_details.get("meta", {}).get("fee", 0)) / Decimal("1000000000")
                        )
                
                return TransactionResult(
                    transaction_id=transaction_id,
                    status="pending"
                )
            
            # Return immediately if no timeout
            return TransactionResult(
                transaction_id=transaction_id,
                status="pending"
            )
        
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            
            return TransactionResult(
                transaction_id="",
                status="failed",
                error=str(e)
            )
    
    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token.
        
        Args:
            token: Token mint address
            
        Returns:
            Optional[Dict[str, Any]]: Token information if successful, None otherwise
        """
        logger.info(f"Getting information for token {token}")
        
        try:
            response = await self._send_rpc_request(
                "getAccountInfo",
                [token, {"encoding": "jsonParsed"}]
            )
            
            if not response or "result" not in response:
                logger.error(f"Failed to get information for token {token}")
                return None
            
            account_info = response["result"]["value"]
            
            if not account_info or account_info.get("data", {}).get("program") != "spl-token":
                logger.error(f"Invalid token account {token}")
                return None
            
            token_info = account_info["data"]["parsed"]["info"]
            
            return {
                "mint": token,
                "decimals": token_info["decimals"],
                "supply": Decimal(token_info["supply"]) / (10 ** token_info["decimals"]),
                "is_initialized": token_info["isInitialized"],
                "freeze_authority": token_info.get("freezeAuthority"),
                "mint_authority": token_info.get("mintAuthority")
            }
        
        except Exception as e:
            logger.error(f"Error getting information for token {token}: {str(e)}")
            return None
    
    async def get_block(self, block_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a block.
        
        Args:
            block_number: Block number (if None, get latest block)
            
        Returns:
            Optional[Dict[str, Any]]: Block information if successful, None otherwise
        """
        logger.info(f"Getting block {block_number if block_number is not None else 'latest'}")
        
        try:
            if block_number is not None:
                # Get specific block
                response = await self._send_rpc_request(
                    "getBlock",
                    [block_number, {"encoding": "jsonParsed"}]
                )
            else:
                # Get latest block
                response = await self._send_rpc_request(
                    "getLatestBlockhash",
                    []
                )
                
                if not response or "result" not in response:
                    logger.error("Failed to get latest block hash")
                    return None
                
                # Get block by hash
                block_hash = response["result"]["value"]["blockhash"]
                
                response = await self._send_rpc_request(
                    "getBlock",
                    [block_hash, {"encoding": "jsonParsed"}]
                )
            
            if not response or "result" not in response:
                logger.error(f"Failed to get block {block_number if block_number is not None else 'latest'}")
                return None
            
            return response["result"]
        
        except Exception as e:
            logger.error(f"Error getting block {block_number if block_number is not None else 'latest'}: {str(e)}")
            return None
    
    # Helper methods
    
    async def _send_rpc_request(
        self,
        method: str,
        params: List[Any],
        retry_count: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Send an RPC request to the blockchain network."""
        if not self.session:
            await self.connect()
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": method,
                "params": params
            }
            
            async with self.session.post(
                self.network_config.rpc_url,
                json=payload,
                timeout=self.network_config.timeout_seconds
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"RPC request failed with status {response.status}: {error_text}")
                    
                    # Retry if not exceeded max retries
                    if retry_count < self.network_config.max_retries:
                        await asyncio.sleep(self.network_config.retry_delay_seconds)
                        return await self._send_rpc_request(method, params, retry_count + 1)
                    
                    return None
        
        except asyncio.TimeoutError:
            logger.error(f"RPC request timed out after {self.network_config.timeout_seconds} seconds")
            
            # Retry if not exceeded max retries
            if retry_count < self.network_config.max_retries:
                await asyncio.sleep(self.network_config.retry_delay_seconds)
                return await self._send_rpc_request(method, params, retry_count + 1)
            
            return None
        
        except Exception as e:
            logger.error(f"Error sending RPC request: {str(e)}")
            
            # Retry if not exceeded max retries
            if retry_count < self.network_config.max_retries:
                await asyncio.sleep(self.network_config.retry_delay_seconds)
                return await self._send_rpc_request(method, params, retry_count + 1)
            
            return None
    
    async def _wait_for_confirmation(
        self,
        transaction_id: str,
        timeout_seconds: int,
        max_retries: int,
        retry_delay_seconds: int,
    ) -> bool:
        """Wait for transaction confirmation."""
        logger.info(f"Waiting for confirmation of transaction {transaction_id}")
        
        start_time = time.time()
        retry_count = 0
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Get transaction status
                tx_details = await self.get_transaction(transaction_id)
                
                if tx_details:
                    logger.info(f"Transaction {transaction_id} confirmed")
                    return True
                
                # Sleep before retrying
                await asyncio.sleep(retry_delay_seconds)
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.warning(f"Exceeded max retries ({max_retries}) for transaction {transaction_id}")
                    return False
            
            except Exception as e:
                logger.error(f"Error checking transaction status: {str(e)}")
                
                # Sleep before retrying
                await asyncio.sleep(retry_delay_seconds)
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.warning(f"Exceeded max retries ({max_retries}) for transaction {transaction_id}")
                    return False
        
        logger.warning(f"Timeout waiting for confirmation of transaction {transaction_id}")
        return False


# Network configurations
MAINNET_CONFIG = NetworkConfig(
    network_id="mainnet-beta",
    name="Solana Mainnet",
    rpc_url="https://api.mainnet-beta.solana.com",
    explorer_url="https://explorer.solana.com",
    is_mainnet=True
)

DEVNET_CONFIG = NetworkConfig(
    network_id="devnet",
    name="Solana Devnet",
    rpc_url="https://api.devnet.solana.com",
    explorer_url="https://explorer.solana.com/?cluster=devnet",
    is_mainnet=False
)

TESTNET_CONFIG = NetworkConfig(
    network_id="testnet",
    name="Solana Testnet",
    rpc_url="https://api.testnet.solana.com",
    explorer_url="https://explorer.solana.com/?cluster=testnet",
    is_mainnet=False
)

LOCALNET_CONFIG = NetworkConfig(
    network_id="localnet",
    name="Solana Localnet",
    rpc_url="http://localhost:8899",
    explorer_url="",
    is_mainnet=False
)


# Singleton instances of BlockchainClient
_clients: Dict[str, BlockchainClient] = {}


async def get_blockchain_client(network_id: str) -> Optional[BlockchainClient]:
    """
    Get a blockchain client for a specific network.
    
    Args:
        network_id: ID of the network (mainnet-beta, devnet, testnet, localnet)
        
    Returns:
        Optional[BlockchainClient]: Blockchain client if successful, None otherwise
    """
    global _clients
    
    if network_id in _clients:
        return _clients[network_id]
    
    # Get network configuration
    network_config = None
    if network_id == "mainnet-beta":
        network_config = MAINNET_CONFIG
    elif network_id == "devnet":
        network_config = DEVNET_CONFIG
    elif network_id == "testnet":
        network_config = TESTNET_CONFIG
    elif network_id == "localnet":
        network_config = LOCALNET_CONFIG
    else:
        logger.error(f"Unknown network ID: {network_id}")
        return None
    
    # Create and connect client
    client = BlockchainClient(network_config)
    if await client.connect():
        _clients[network_id] = client
        return client
    
    return None


async def close_all_clients() -> None:
    """Close all blockchain clients."""
    global _clients
    
    for network_id, client in _clients.items():
        logger.info(f"Closing client for network {network_id}")
        await client.disconnect()
    
    _clients = {}


# Example usage
if __name__ == "__main__":
    async def example():
        # Get blockchain client for devnet
        client = await get_blockchain_client("devnet")
        
        if not client:
            print("Failed to get blockchain client")
            return
        
        # Get SOL balance for an address
        address = "9B5XszUGdMaxCZ7uSQhPzdks5ZQSmWxrmzCSvtJ6Ns6g"  # Example address
        balance = await client.get_balance(address)
        print(f"SOL balance for {address}: {balance}")
        
        # Get latest block
        block = await client.get_block()
        print(f"Latest block: {block}")
        
        # Close all clients
        await close_all_clients()
    
    # Run example
    asyncio.run(example())