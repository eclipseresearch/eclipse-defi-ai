#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for Blockchain Module
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

from core.blockchain import (
    NetworkConfig, TransactionConfig, TransactionResult,
    BlockchainClient, get_blockchain_client,
    MAINNET_CONFIG, DEVNET_CONFIG, TESTNET_CONFIG, LOCALNET_CONFIG
)


class TestNetworkConfig(unittest.TestCase):
    """Test cases for NetworkConfig class."""

    def test_network_config_creation(self):
        """Test creating a NetworkConfig instance."""
        config = NetworkConfig(
            network_id="test-network",
            name="Test Network",
            rpc_url="https://api.test.com",
            explorer_url="https://explorer.test.com",
            is_mainnet=False,
            timeout_seconds=60,
            max_retries=5,
            retry_delay_seconds=2
        )
        
        self.assertEqual(config.network_id, "test-network")
        self.assertEqual(config.name, "Test Network")
        self.assertEqual(config.rpc_url, "https://api.test.com")
        self.assertEqual(config.explorer_url, "https://explorer.test.com")
        self.assertFalse(config.is_mainnet)
        self.assertEqual(config.timeout_seconds, 60)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.retry_delay_seconds, 2)


class TestTransactionConfig(unittest.TestCase):
    """Test cases for TransactionConfig class."""

    def test_transaction_config_creation(self):
        """Test creating a TransactionConfig instance."""
        config = TransactionConfig(
            max_fee=Decimal("0.01"),
            priority_fee=Decimal("0.001"),
            timeout_seconds=120,
            skip_preflight=True,
            max_retries=3,
            retry_delay_seconds=5
        )
        
        self.assertEqual(config.max_fee, Decimal("0.01"))
        self.assertEqual(config.priority_fee, Decimal("0.001"))
        self.assertEqual(config.timeout_seconds, 120)
        self.assertTrue(config.skip_preflight)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay_seconds, 5)


class TestTransactionResult(unittest.TestCase):
    """Test cases for TransactionResult class."""

    def test_transaction_result_creation(self):
        """Test creating a TransactionResult instance."""
        result = TransactionResult(
            transaction_id="tx123",
            status="confirmed",
            block_hash="block456",
            block_time=1620000000,
            fee=Decimal("0.000005"),
            error=None
        )
        
        self.assertEqual(result.transaction_id, "tx123")
        self.assertEqual(result.status, "confirmed")
        self.assertEqual(result.block_hash, "block456")
        self.assertEqual(result.block_time, 1620000000)
        self.assertEqual(result.fee, Decimal("0.000005"))
        self.assertIsNone(result.error)


class TestBlockchainClient(unittest.TestCase):
    """Test cases for BlockchainClient class."""

    def setUp(self):
        """Set up test environment."""
        self.network_config = NetworkConfig(
            network_id="test-network",
            name="Test Network",
            rpc_url="https://api.test.com",
            explorer_url="https://explorer.test.com"
        )
        
        self.client = BlockchainClient(self.network_config)
    
    @patch('aiohttp.ClientSession.post')
    async def async_test_connect(self, mock_post):
        """Test connecting to the blockchain network."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.json.return_value = asyncio.Future()
        mock_response.json.return_value.set_result({"result": "ok"})
        
        mock_post.return_value = mock_response
        
        # Connect to network
        result = await self.client.connect()
        
        # Verify results
        self.assertTrue(result)
        self.assertIsNotNone(self.client.session)
        
        # Verify mock was called
        mock_post.assert_called_once()
    
    def test_connect(self):
        """Test connecting to the blockchain network."""
        asyncio.run(self.async_test_connect())
    
    @patch('aiohttp.ClientSession.close')
    async def async_test_disconnect(self, mock_close):
        """Test disconnecting from the blockchain network."""
        # Create session
        self.client.session = MagicMock()
        
        # Mock close method
        mock_close.return_value = asyncio.Future()
        mock_close.return_value.set_result(None)
        
        # Disconnect from network
        result = await self.client.disconnect()
        
        # Verify results
        self.assertTrue(result)
        self.assertIsNone(self.client.session)
        
        # Verify mock was called
        mock_close.assert_called_once()
    
    def test_disconnect(self):
        """Test disconnecting from the blockchain network."""
        asyncio.run(self.async_test_disconnect())
    
    @patch('core.blockchain.BlockchainClient._send_rpc_request')
    async def async_test_get_balance(self, mock_send_request):
        """Test getting balance."""
        # Mock response
        mock_response = {
            "result": {
                "value": 1000000000  # 1 SOL in lamports
            }
        }
        mock_send_request.return_value = asyncio.Future()
        mock_send_request.return_value.set_result(mock_response)
        
        # Get balance
        address = "test_address"
        balance = await self.client.get_balance(address)
        
        # Verify results
        self.assertEqual(balance, Decimal("1"))  # 1 SOL
        
        # Verify mock was called
        mock_send_request.assert_called_once_with("getBalance", [address])
    
    def test_get_balance(self):
        """Test getting balance."""
        asyncio.run(self.async_test_get_balance())
    
    @patch('core.blockchain.BlockchainClient._send_rpc_request')
    async def async_test_get_transaction(self, mock_send_request):
        """Test getting transaction details."""
        # Mock response
        mock_response = {
            "result": {
                "transaction": {
                    "signatures": ["sig123"]
                },
                "meta": {
                    "fee": 5000
                }
            }
        }
        mock_send_request.return_value = asyncio.Future()
        mock_send_request.return_value.set_result(mock_response)
        
        # Get transaction
        tx_id = "tx123"
        tx_details = await self.client.get_transaction(tx_id)
        
        # Verify results
        self.assertEqual(tx_details, mock_response["result"])
        
        # Verify mock was called
        mock_send_request.assert_called_once()
    
    def test_get_transaction(self):
        """Test getting transaction details."""
        asyncio.run(self.async_test_get_transaction())
    
    @patch('core.blockchain.BlockchainClient._send_rpc_request')
    @patch('core.blockchain.BlockchainClient._wait_for_confirmation')
    @patch('core.blockchain.BlockchainClient.get_transaction')
    async def async_test_send_transaction(self, mock_get_tx, mock_wait, mock_send_request):
        """Test sending a transaction."""
        # Mock responses
        mock_send_response = {
            "result": "tx123"
        }
        mock_send_request.return_value = asyncio.Future()
        mock_send_request.return_value.set_result(mock_send_response)
        
        mock_wait.return_value = asyncio.Future()
        mock_wait.return_value.set_result(True)
        
        mock_tx_details = {
            "blockhash": "block456",
            "blockTime": 1620000000,
            "meta": {
                "fee": 5000
            }
        }
        mock_get_tx.return_value = asyncio.Future()
        mock_get_tx.return_value.set_result(mock_tx_details)
        
        # Send transaction
        tx_data = "base64_encoded_transaction"
        config = TransactionConfig(timeout_seconds=60)
        result = await self.client.send_transaction(tx_data, config)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result.transaction_id, "tx123")
        self.assertEqual(result.status, "confirmed")
        self.assertEqual(result.block_hash, "block456")
        self.assertEqual(result.block_time, 1620000000)
        self.assertEqual(result.fee, Decimal("0.000005"))  # 5000 lamports
        
        # Verify mocks were called
        mock_send_request.assert_called_once()
        mock_wait.assert_called_once()
        mock_get_tx.assert_called_once()
    
    def test_send_transaction(self):
        """Test sending a transaction."""
        asyncio.run(self.async_test_send_transaction())
    
    def test_network_configs(self):
        """Test predefined network configurations."""
        # Test mainnet config
        self.assertEqual(MAINNET_CONFIG.network_id, "mainnet-beta")
        self.assertEqual(MAINNET_CONFIG.name, "Solana Mainnet")
        self.assertEqual(MAINNET_CONFIG.rpc_url, "https://api.mainnet-beta.solana.com")
        self.assertTrue(MAINNET_CONFIG.is_mainnet)
        
        # Test devnet config
        self.assertEqual(DEVNET_CONFIG.network_id, "devnet")
        self.assertEqual(DEVNET_CONFIG.name, "Solana Devnet")
        self.assertEqual(DEVNET_CONFIG.rpc_url, "https://api.devnet.solana.com")
        self.assertFalse(DEVNET_CONFIG.is_mainnet)
        
        # Test testnet config
        self.assertEqual(TESTNET_CONFIG.network_id, "testnet")
        self.assertEqual(TESTNET_CONFIG.name, "Solana Testnet")
        self.assertEqual(TESTNET_CONFIG.rpc_url, "https://api.testnet.solana.com")
        self.assertFalse(TESTNET_CONFIG.is_mainnet)
        
        # Test localnet config
        self.assertEqual(LOCALNET_CONFIG.network_id, "localnet")
        self.assertEqual(LOCALNET_CONFIG.name, "Solana Localnet")
        self.assertEqual(LOCALNET_CONFIG.rpc_url, "http://localhost:8899")
        self.assertFalse(LOCALNET_CONFIG.is_mainnet)
    
    @patch('core.blockchain.BlockchainClient.connect')
    async def async_test_get_blockchain_client(self, mock_connect):
        """Test getting a blockchain client."""
        # Mock connect method
        mock_connect.return_value = asyncio.Future()
        mock_connect.return_value.set_result(True)
        
        # Get client
        client = await get_blockchain_client("devnet")
        
        # Verify results
        self.assertIsNotNone(client)
        self.assertEqual(client.network_config.network_id, "devnet")
        
        # Verify mock was called
        mock_connect.assert_called_once()
    
    def test_get_blockchain_client(self):
        """Test getting a blockchain client."""
        asyncio.run(self.async_test_get_blockchain_client())


if __name__ == '__main__':
    unittest.main()