#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for Data Module
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import asyncio
import tempfile
import shutil
import sqlite3
from unittest.mock import patch, MagicMock
import pandas as pd
from decimal import Decimal

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.data import DataManager, DataSource, DataQuery, DataResult, get_data_manager


class TestDataSource(unittest.TestCase):
    """Test cases for DataSource class."""

    def test_data_source_creation(self):
        """Test creating a DataSource instance."""
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            },
            metadata={
                "description": "Test database source"
            }
        )
        
        self.assertEqual(source.source_id, "test_source")
        self.assertEqual(source.name, "Test Source")
        self.assertEqual(source.type, "database")
        self.assertEqual(source.connection_info["type"], "sqlite")
        self.assertEqual(source.connection_info["path"], ":memory:")
        self.assertEqual(source.metadata["description"], "Test database source")


class TestDataQuery(unittest.TestCase):
    """Test cases for DataQuery class."""

    def test_data_query_creation(self):
        """Test creating a DataQuery instance."""
        query = DataQuery(
            query_id="test_query",
            source_id="test_source",
            query_type="sql",
            query_params={
                "query": "SELECT * FROM test",
                "params": []
            },
            metadata={
                "description": "Test SQL query"
            }
        )
        
        self.assertEqual(query.query_id, "test_query")
        self.assertEqual(query.source_id, "test_source")
        self.assertEqual(query.query_type, "sql")
        self.assertEqual(query.query_params["query"], "SELECT * FROM test")
        self.assertEqual(query.query_params["params"], [])
        self.assertEqual(query.metadata["description"], "Test SQL query")


class TestDataResult(unittest.TestCase):
    """Test cases for DataResult class."""

    def test_data_result_creation(self):
        """Test creating a DataResult instance."""
        result = DataResult(
            query_id="test_query",
            source_id="test_source",
            timestamp=1620000000,
            data=[{"id": 1, "name": "Test"}],
            metadata={
                "row_count": 1
            }
        )
        
        self.assertEqual(result.query_id, "test_query")
        self.assertEqual(result.source_id, "test_source")
        self.assertEqual(result.timestamp, 1620000000)
        self.assertEqual(result.data[0]["id"], 1)
        self.assertEqual(result.data[0]["name"], "Test")
        self.assertEqual(result.metadata["row_count"], 1)


class TestDataManager(unittest.TestCase):
    """Test cases for DataManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for data
        self.test_data_dir = tempfile.mkdtemp()
        
        # Create data manager
        self.data_manager = DataManager(self.test_data_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        shutil.rmtree(self.test_data_dir)
    
    async def async_test_register_source(self):
        """Test registering a data source."""
        # Create source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        # Register source
        result = await self.data_manager.register_source(source)
        
        # Verify results
        self.assertTrue(result)
        self.assertIn("test_source", self.data_manager.sources)
        
        # Check if sources file was created
        sources_file = os.path.join(self.test_data_dir, "sources.json")
        self.assertTrue(os.path.exists(sources_file))
    
    def test_register_source(self):
        """Test registering a data source."""
        asyncio.run(self.async_test_register_source())
    
    async def async_test_unregister_source(self):
        """Test unregistering a data source."""
        # Register source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        await self.data_manager.register_source(source)
        
        # Unregister source
        result = await self.data_manager.unregister_source("test_source")
        
        # Verify results
        self.assertTrue(result)
        self.assertNotIn("test_source", self.data_manager.sources)
    
    def test_unregister_source(self):
        """Test unregistering a data source."""
        asyncio.run(self.async_test_unregister_source())
    
    async def async_test_get_source(self):
        """Test getting a data source."""
        # Register source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        await self.data_manager.register_source(source)
        
        # Get source
        retrieved_source = await self.data_manager.get_source("test_source")
        
        # Verify results
        self.assertIsNotNone(retrieved_source)
        self.assertEqual(retrieved_source.source_id, "test_source")
        self.assertEqual(retrieved_source.name, "Test Source")
    
    def test_get_source(self):
        """Test getting a data source."""
        asyncio.run(self.async_test_get_source())
    
    async def async_test_list_sources(self):
        """Test listing data sources."""
        # Register multiple sources
        source1 = DataSource(
            source_id="source1",
            name="Source 1",
            type="database",
            connection_info={"type": "sqlite", "path": ":memory:"}
        )
        
        source2 = DataSource(
            source_id="source2",
            name="Source 2",
            type="file",
            connection_info={"path": "test.csv"}
        )
        
        await self.data_manager.register_source(source1)
        await self.data_manager.register_source(source2)
        
        # List sources
        sources = await self.data_manager.list_sources()
        
        # Verify results
        self.assertEqual(len(sources), 2)
        source_ids = [s.source_id for s in sources]
        self.assertIn("source1", source_ids)
        self.assertIn("source2", source_ids)
    
    def test_list_sources(self):
        """Test listing data sources."""
        asyncio.run(self.async_test_list_sources())
    
    @patch('core.data.DataManager._connect_database')
    async def async_test_connect(self, mock_connect):
        """Test connecting to a data source."""
        # Register source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        await self.data_manager.register_source(source)
        
        # Mock connection
        mock_connection = MagicMock()
        mock_connect.return_value = asyncio.Future()
        mock_connect.return_value.set_result(mock_connection)
        
        # Connect to source
        result = await self.data_manager.connect("test_source")
        
        # Verify results
        self.assertTrue(result)
        self.assertIn("test_source", self.data_manager.connections)
        self.assertEqual(self.data_manager.connections["test_source"], mock_connection)
        
        # Verify mock was called
        mock_connect.assert_called_once()
    
    def test_connect(self):
        """Test connecting to a data source."""
        asyncio.run(self.async_test_connect())
    
    @patch('core.data.DataManager._close_database_connection')
    async def async_test_close_connection(self, mock_close):
        """Test closing a connection to a data source."""
        # Register source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        await self.data_manager.register_source(source)
        
        # Add mock connection
        mock_connection = MagicMock()
        self.data_manager.connections["test_source"] = mock_connection
        
        # Close connection
        result = await self.data_manager.close_connection("test_source")
        
        # Verify results
        self.assertTrue(result)
        self.assertNotIn("test_source", self.data_manager.connections)
        
        # Verify mock was called
        mock_close.assert_called_once_with(mock_connection)
    
    def test_close_connection(self):
        """Test closing a connection to a data source."""
        asyncio.run(self.async_test_close_connection())
    
    @patch('core.data.DataManager._execute_sql_query')
    async def async_test_execute_query(self, mock_execute):
        """Test executing a data query."""
        # Register source
        source = DataSource(
            source_id="test_source",
            name="Test Source",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": ":memory:"
            }
        )
        
        await self.data_manager.register_source(source)
        
        # Add mock connection
        mock_connection = MagicMock()
        self.data_manager.connections["test_source"] = mock_connection
        
        # Mock query execution
        mock_data = [{"id": 1, "name": "Test"}]
        mock_execute.return_value = asyncio.Future()
        mock_execute.return_value.set_result(mock_data)
        
        # Create query
        query = DataQuery(
            query_id="test_query",
            source_id="test_source",
            query_type="sql",
            query_params={
                "query": "SELECT * FROM test"
            }
        )
        
        # Execute query
        result = await self.data_manager.execute_query(query)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result.query_id, "test_query")
        self.assertEqual(result.source_id, "test_source")
        self.assertEqual(result.data, mock_data)
        
        # Verify mock was called
        mock_execute.assert_called_once_with(mock_connection, query.query_params)
    
    def test_execute_query(self):
        """Test executing a data query."""
        asyncio.run(self.async_test_execute_query())
    
    async def async_test_save_load_data(self):
        """Test saving and loading data."""
        # Create test data
        data = [
            {"id": 1, "name": "Item 1", "value": 10.5},
            {"id": 2, "name": "Item 2", "value": 20.75}
        ]
        
        # Save data as CSV
        csv_path = os.path.join(self.test_data_dir, "test.csv")
        result = await self.data_manager.save_data(data, csv_path, "csv")
        
        # Verify results
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))
        
        # Load data from CSV
        loaded_data = await self.data_manager.load_data(csv_path)
        
        # Verify loaded data
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data.iloc[0]["id"], 1)
        self.assertEqual(loaded_data.iloc[0]["name"], "Item 1")
        self.assertEqual(loaded_data.iloc[0]["value"], 10.5)
        
        # Save data as JSON
        json_path = os.path.join(self.test_data_dir, "test.json")
        result = await self.data_manager.save_data(data, json_path, "json")
        
        # Verify results
        self.assertTrue(result)
        self.assertTrue(os.path.exists(json_path))
        
        # Load data from JSON
        loaded_json = await self.data_manager.load_data(json_path)
        
        # Verify loaded data
        self.assertIsNotNone(loaded_json)
        self.assertEqual(len(loaded_json), 2)
        self.assertEqual(loaded_json[0]["id"], 1)
        self.assertEqual(loaded_json[0]["name"], "Item 1")
        self.assertEqual(loaded_json[0]["value"], 10.5)
    
    def test_save_load_data(self):
        """Test saving and loading data."""
        asyncio.run(self.async_test_save_load_data())
    
    def test_get_data_manager(self):
        """Test getting the singleton data manager."""
        # Get data manager
        manager1 = get_data_manager(self.test_data_dir)
        manager2 = get_data_manager(self.test_data_dir)
        
        # Verify it's the same instance
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()