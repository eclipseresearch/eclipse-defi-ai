#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Core Data Module
Author: ECLIPSEMOON
"""

import os
import json
import logging
import sqlite3
import csv
import pickle
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

import pandas as pd
import numpy as np
from pydantic import BaseModel

# Setup logger
logger = logging.getLogger("core.data")


class DataSource(BaseModel):
    """Model representing a data source."""
    
    source_id: str
    name: str
    type: str  # file, database, api
    connection_info: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class DataQuery(BaseModel):
    """Model representing a data query."""
    
    query_id: str
    source_id: str
    query_type: str  # sql, file_read, api_call
    query_params: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class DataResult(BaseModel):
    """Model representing the result of a data query."""
    
    query_id: str
    source_id: str
    timestamp: int
    data: Any
    metadata: Dict[str, Any] = {}


class DataManager:
    """Manager for data sources and queries."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the data manager.
        
        Args:
            data_dir: Directory to store data files (if None, use default)
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".eclipsemoon", "data")
        self.sources: Dict[str, DataSource] = {}
        self.connections: Dict[str, Any] = {}
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def register_source(self, source: DataSource) -> bool:
        """
        Register a data source.
        
        Args:
            source: Data source to register
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Registering data source: {source.name} ({source.source_id})")
        
        try:
            # Save source configuration
            self.sources[source.source_id] = source
            
            # Save to file
            sources_file = os.path.join(self.data_dir, "sources.json")
            
            # Load existing sources
            existing_sources = {}
            if os.path.exists(sources_file):
                with open(sources_file, 'r') as f:
                    existing_sources = json.load(f)
            
            # Update with new source
            existing_sources[source.source_id] = self._prepare_for_json(source.dict())
            
            # Save updated sources
            with open(sources_file, 'w') as f:
                json.dump(existing_sources, f, indent=2)
            
            logger.info(f"Data source {source.source_id} registered successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error registering data source {source.source_id}: {str(e)}")
            return False
    
    async def unregister_source(self, source_id: str) -> bool:
        """
        Unregister a data source.
        
        Args:
            source_id: ID of the data source to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Unregistering data source: {source_id}")
        
        try:
            # Close connection if open
            await self.close_connection(source_id)
            
            # Remove from memory
            if source_id in self.sources:
                del self.sources[source_id]
            
            # Update sources file
            sources_file = os.path.join(self.data_dir, "sources.json")
            
            if os.path.exists(sources_file):
                with open(sources_file, 'r') as f:
                    existing_sources = json.load(f)
                
                if source_id in existing_sources:
                    del existing_sources[source_id]
                
                with open(sources_file, 'w') as f:
                    json.dump(existing_sources, f, indent=2)
            
            logger.info(f"Data source {source_id} unregistered successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error unregistering data source {source_id}: {str(e)}")
            return False
    
    async def get_source(self, source_id: str) -> Optional[DataSource]:
        """
        Get a data source.
        
        Args:
            source_id: ID of the data source
            
        Returns:
            Optional[DataSource]: Data source if found, None otherwise
        """
        logger.info(f"Getting data source: {source_id}")
        
        # Check if source is in memory
        if source_id in self.sources:
            return self.sources[source_id]
        
        # Try to load from file
        sources_file = os.path.join(self.data_dir, "sources.json")
        
        if os.path.exists(sources_file):
            try:
                with open(sources_file, 'r') as f:
                    existing_sources = json.load(f)
                
                if source_id in existing_sources:
                    source_dict = existing_sources[source_id]
                    source = DataSource(**source_dict)
                    self.sources[source_id] = source
                    return source
            
            except Exception as e:
                logger.error(f"Error loading data source {source_id}: {str(e)}")
        
        logger.error(f"Data source {source_id} not found")
        return None
    
    async def list_sources(self) -> List[DataSource]:
        """
        List all registered data sources.
        
        Returns:
            List[DataSource]: List of registered data sources
        """
        logger.info("Listing registered data sources")
        
        sources = []
        
        # Load sources from file
        sources_file = os.path.join(self.data_dir, "sources.json")
        
        if os.path.exists(sources_file):
            try:
                with open(sources_file, 'r') as f:
                    existing_sources = json.load(f)
                
                for source_id, source_dict in existing_sources.items():
                    source = DataSource(**source_dict)
                    self.sources[source_id] = source
                    sources.append(source)
            
            except Exception as e:
                logger.error(f"Error loading data sources: {str(e)}")
        
        return sources
    
    async def connect(self, source_id: str) -> bool:
        """
        Connect to a data source.
        
        Args:
            source_id: ID of the data source
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Connecting to data source: {source_id}")
        
        # Check if already connected
        if source_id in self.connections:
            logger.info(f"Already connected to data source {source_id}")
            return True
        
        # Get source
        source = await self.get_source(source_id)
        
        if not source:
            logger.error(f"Data source {source_id} not found")
            return False
        
        try:
            # Connect based on source type
            if source.type == "database":
                connection = await self._connect_database(source)
            elif source.type == "file":
                connection = await self._connect_file(source)
            elif source.type == "api":
                connection = await self._connect_api(source)
            else:
                logger.error(f"Unsupported data source type: {source.type}")
                return False
            
            if connection:
                self.connections[source_id] = connection
                logger.info(f"Connected to data source {source_id}")
                return True
            else:
                logger.error(f"Failed to connect to data source {source_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error connecting to data source {source_id}: {str(e)}")
            return False
    
    async def close_connection(self, source_id: str) -> bool:
        """
        Close connection to a data source.
        
        Args:
            source_id: ID of the data source
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Closing connection to data source: {source_id}")
        
        # Check if connected
        if source_id not in self.connections:
            logger.info(f"Not connected to data source {source_id}")
            return True
        
        try:
            # Get source
            source = await self.get_source(source_id)
            
            if not source:
                logger.error(f"Data source {source_id} not found")
                return False
            
            # Close connection based on source type
            connection = self.connections[source_id]
            
            if source.type == "database":
                await self._close_database_connection(connection)
            elif source.type == "file":
                await self._close_file_connection(connection)
            elif source.type == "api":
                await self._close_api_connection(connection)
            
            # Remove from connections
            del self.connections[source_id]
            
            logger.info(f"Connection to data source {source_id} closed")
            return True
        
        except Exception as e:
            logger.error(f"Error closing connection to data source {source_id}: {str(e)}")
            return False
    
    async def execute_query(
        self,
        query: DataQuery,
    ) -> Optional[DataResult]:
        """
        Execute a data query.
        
        Args:
            query: Data query to execute
            
        Returns:
            Optional[DataResult]: Query result if successful, None otherwise
        """
        logger.info(f"Executing query: {query.query_id} on source {query.source_id}")
        
        # Connect to source if not connected
        if query.source_id not in self.connections:
            if not await self.connect(query.source_id):
                logger.error(f"Failed to connect to data source {query.source_id}")
                return None
        
        try:
            # Get source
            source = await self.get_source(query.source_id)
            
            if not source:
                logger.error(f"Data source {query.source_id} not found")
                return None
            
            # Execute query based on query type
            connection = self.connections[query.source_id]
            
            if query.query_type == "sql":
                data = await self._execute_sql_query(connection, query.query_params)
            elif query.query_type == "file_read":
                data = await self._execute_file_read(connection, query.query_params)
            elif query.query_type == "api_call":
                data = await self._execute_api_call(connection, query.query_params)
            else:
                logger.error(f"Unsupported query type: {query.query_type}")
                return None
            
            # Create result
            result = DataResult(
                query_id=query.query_id,
                source_id=query.source_id,
                timestamp=int(datetime.now().timestamp()),
                data=data,
                metadata=query.metadata
            )
            
            logger.info(f"Query {query.query_id} executed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error executing query {query.query_id}: {str(e)}")
            return None
    
    async def save_data(
        self,
        data: Any,
        file_path: str,
        format: str = "csv",
    ) -> bool:
        """
        Save data to a file.
        
        Args:
            data: Data to save
            file_path: Path to save the data to
            format: Format to save as (csv, json, pickle)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Saving data to {file_path} in {format} format")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save data based on format
            if format.lower() == "csv":
                if isinstance(data, pd.DataFrame):
                    data.to_csv(file_path, index=False)
                elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    df = pd.DataFrame(data)
                    df.to_csv(file_path, index=False)
                else:
                    with open(file_path, 'w', newline='') as f:
                        if isinstance(data, list) and all(isinstance(item, list) for item in data):
                            writer = csv.writer(f)
                            writer.writerows(data)
                        else:
                            logger.error(f"Unsupported data type for CSV format: {type(data)}")
                            return False
            
            elif format.lower() == "json":
                with open(file_path, 'w') as f:
                    json.dump(self._prepare_for_json(data), f, indent=2)
            
            elif format.lower() == "pickle":
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            logger.info(f"Data saved successfully to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {str(e)}")
            return False
    
    async def load_data(
        self,
        file_path: str,
        format: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Load data from a file.
        
        Args:
            file_path: Path to load the data from
            format: Format to load as (csv, json, pickle, auto)
            
        Returns:
            Optional[Any]: Loaded data if successful, None otherwise
        """
        logger.info(f"Loading data from {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} not found")
            return None
        
        try:
            # Determine format if not provided
            if format is None:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".csv":
                    format = "csv"
                elif ext == ".json":
                    format = "json"
                elif ext in (".pkl", ".pickle"):
                    format = "pickle"
                else:
                    logger.error(f"Could not determine format for file {file_path}")
                    return None
            
            # Load data based on format
            if format.lower() == "csv":
                data = pd.read_csv(file_path)
            
            elif format.lower() == "json":
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Convert string values to Decimal where needed
                data = self._convert_decimal_strings(data)
            
            elif format.lower() == "pickle":
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            
            else:
                logger.error(f"Unsupported format: {format}")
                return None
            
            logger.info(f"Data loaded successfully from {file_path}")
            return data
        
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return None
    
    # Helper methods for connecting to different data sources
    
    async def _connect_database(self, source: DataSource) -> Optional[Any]:
        """Connect to a database data source."""
        connection_info = source.connection_info
        
        if "type" not in connection_info:
            logger.error(f"Missing database type in connection info for source {source.source_id}")
            return None
        
        db_type = connection_info["type"]
        
        if db_type == "sqlite":
            # Connect to SQLite database
            db_path = connection_info.get("path")
            
            if not db_path:
                logger.error(f"Missing database path for SQLite source {source.source_id}")
                return None
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            
            # Connect to database
            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            
            return connection
        
        elif db_type == "postgres":
            # For a real implementation, this would connect to a PostgreSQL database
            # using a library like psycopg2 or asyncpg
            logger.error(f"PostgreSQL connections not implemented")
            return None
        
        else:
            logger.error(f"Unsupported database type: {db_type}")
            return None
    
    async def _connect_file(self, source: DataSource) -> Optional[Any]:
        """Connect to a file data source."""
        connection_info = source.connection_info
        
        if "path" not in connection_info:
            logger.error(f"Missing file path in connection info for source {source.source_id}")
            return None
        
        file_path = connection_info["path"]
        
        # For file sources, the "connection" is just the file path
        return file_path
    
    async def _connect_api(self, source: DataSource) -> Optional[Any]:
        """Connect to an API data source."""
        connection_info = source.connection_info
        
        if "url" not in connection_info:
            logger.error(f"Missing API URL in connection info for source {source.source_id}")
            return None
        
        # For API sources, the "connection" is a dictionary with API details
        return connection_info
    
    async def _close_database_connection(self, connection: Any) -> None:
        """Close a database connection."""
        if isinstance(connection, sqlite3.Connection):
            connection.close()
    
    async def _close_file_connection(self, connection: Any) -> None:
        """Close a file connection."""
        # Nothing to do for file connections
        pass
    
    async def _close_api_connection(self, connection: Any) -> None:
        """Close an API connection."""
        # Nothing to do for API connections
        pass
    
    async def _execute_sql_query(
        self,
        connection: Any,
        query_params: Dict[str, Any],
    ) -> Any:
        """Execute an SQL query."""
        if "query" not in query_params:
            logger.error("Missing query in query parameters")
            return None
        
        query = query_params["query"]
        params = query_params.get("params", [])
        
        if isinstance(connection, sqlite3.Connection):
            cursor = connection.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(("SELECT", "PRAGMA")):
                # Fetch results for SELECT queries
                columns = [column[0] for column in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
            else:
                # Commit for other queries
                connection.commit()
                return {"affected_rows": cursor.rowcount}
        
        return None
    
    async def _execute_file_read(
        self,
        connection: Any,
        query_params: Dict[str, Any],
    ) -> Any:
        """Execute a file read query."""
        file_path = connection
        format = query_params.get("format", "auto")
        
        return await self.load_data(file_path, format)
    
    async def _execute_api_call(
        self,
        connection: Any,
        query_params: Dict[str, Any],
    ) -> Any:
        """Execute an API call query."""
        # This would make an API call using the connection info
        # Placeholder implementation
        logger.error("API call queries not implemented")
        return None
    
    def _prepare_for_json(self, data: Any) -> Any:
        """Prepare data for JSON serialization by converting Decimal objects to strings."""
        if isinstance(data, dict):
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")
        elif isinstance(data, np.ndarray):
            return data.tolist()
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


# Singleton instance of DataManager
_data_manager = None


def get_data_manager(data_dir: Optional[str] = None) -> DataManager:
    """
    Get the singleton instance of DataManager.
    
    Args:
        data_dir: Directory to store data files (if None, use default)
        
    Returns:
        DataManager: Singleton instance of DataManager
    """
    global _data_manager
    
    if _data_manager is None:
        _data_manager = DataManager(data_dir)
    
    return _data_manager


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    async def example():
        # Get data manager
        data_manager = get_data_manager()
        
        # Register a SQLite database source
        db_path = os.path.join(data_manager.data_dir, "example.db")
        
        source = DataSource(
            source_id="example_db",
            name="Example Database",
            type="database",
            connection_info={
                "type": "sqlite",
                "path": db_path
            },
            metadata={
                "description": "Example SQLite database for testing"
            }
        )
        
        await data_manager.register_source(source)
        
        # Connect to the source
        await data_manager.connect("example_db")
        
        # Create a table
        create_table_query = DataQuery(
            query_id="create_table",
            source_id="example_db",
            query_type="sql",
            query_params={
                "query": """
                CREATE TABLE IF NOT EXISTS example (
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
            source_id="example_db",
            query_type="sql",
            query_params={
                "query": "INSERT INTO example (name, value) VALUES (?, ?)",
                "params": ["Example", 123.45]
            }
        )
        
        await data_manager.execute_query(insert_query)
        
        # Query data
        select_query = DataQuery(
            query_id="select_data",
            source_id="example_db",
            query_type="sql",
            query_params={
                "query": "SELECT * FROM example"
            }
        )
        
        result = await data_manager.execute_query(select_query)
        
        if result:
            print("Query result:", result.data)
        
        # Save data to CSV
        csv_path = os.path.join(data_manager.data_dir, "example.csv")
        await data_manager.save_data(result.data, csv_path, "csv")
        
        # Load data from CSV
        loaded_data = await data_manager.load_data(csv_path)
        print("Loaded data:", loaded_data)
        
        # Close connection
        await data_manager.close_connection("example_db")
    
    # Run example
    asyncio.run(example())