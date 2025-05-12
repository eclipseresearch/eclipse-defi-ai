#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for Utils Module
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import time
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.utils import (
    Result, Timer, setup_logging, retry, format_decimal, parse_decimal,
    timestamp_to_datetime, datetime_to_timestamp, format_datetime, parse_datetime,
    json_serialize, to_json, from_json, safe_divide, truncate_string,
    get_exception_traceback, is_valid_json, get_environment_variable, chunks
)


class TestResult(unittest.TestCase):
    """Test cases for Result class."""

    def test_ok_result(self):
        """Test creating a successful result."""
        # Create successful result
        value = "test_value"
        message = "Operation successful"
        result = Result.ok(value, message)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.value, value)
        self.assertIsNone(result.error)
        self.assertEqual(result.message, message)
        self.assertTrue(bool(result))
    
    def test_err_result(self):
        """Test creating an unsuccessful result."""
        # Create unsuccessful result
        error = ValueError("Test error")
        message = "Operation failed"
        result = Result.err(error, message)
        
        # Verify result
        self.assertFalse(result.success)
        self.assertIsNone(result.value)
        self.assertEqual(result.error, error)
        self.assertEqual(result.message, message)
        self.assertFalse(bool(result))


class TestTimer(unittest.TestCase):
    """Test cases for Timer class."""

    def test_timer_context_manager(self):
        """Test using Timer as a context manager."""
        # Use timer as context manager
        with Timer("Test timer") as timer:
            time.sleep(0.1)
        
        # Verify timer
        self.assertIsNotNone(timer.start_time)
        self.assertIsNotNone(timer.end_time)
        self.assertGreaterEqual(timer.elapsed(), 0.1)
    
    def test_timer_manual(self):
        """Test using Timer manually."""
        # Create timer
        timer = Timer("Manual timer")
        
        # Start timer
        timer.start()
        time.sleep(0.1)
        
        # Get elapsed time
        elapsed1 = timer.elapsed()
        self.assertGreaterEqual(elapsed1, 0.1)
        
        # Stop timer
        elapsed2 = timer.stop()
        self.assertGreaterEqual(elapsed2, 0.1)
        
        # Verify timer
        self.assertIsNotNone(timer.start_time)
        self.assertIsNotNone(timer.end_time)
        self.assertEqual(timer.elapsed(), elapsed2)


class TestRetry(unittest.TestCase):
    """Test cases for retry decorator."""

    def test_retry_success(self):
        """Test retry decorator with successful function."""
        # Create function that succeeds
        @retry(max_attempts=3, delay=0.1)
        def successful_function():
            return "Success"
        
        # Call function
        result = successful_function()
        
        # Verify result
        self.assertEqual(result, "Success")
    
    def test_retry_failure(self):
        """Test retry decorator with failing function."""
        # Create function that always fails
        @retry(max_attempts=3, delay=0.1)
        def failing_function():
            raise ValueError("Test error")
        
        # Call function and expect exception
        with self.assertRaises(ValueError):
            failing_function()
    
    def test_retry_eventual_success(self):
        """Test retry decorator with function that eventually succeeds."""
        # Create counter
        attempts = [0]
        
        # Create function that fails twice then succeeds
        @retry(max_attempts=3, delay=0.1)
        def eventual_success():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Test error")
            return "Success"
        
        # Call function
        result = eventual_success()
        
        # Verify result
        self.assertEqual(result, "Success")
        self.assertEqual(attempts[0], 3)


class TestFormatting(unittest.TestCase):
    """Test cases for formatting functions."""

    def test_format_decimal(self):
        """Test formatting decimal values."""
        # Format decimal with default precision
        value = Decimal("123.45678901234567890")
        formatted = format_decimal(value)
        self.assertEqual(formatted, "123.45678901")
        
        # Format decimal with custom precision
        formatted = format_decimal(value, precision=4)
        self.assertEqual(formatted, "123.4568")
        
        # Format decimal with trailing zeros
        value = Decimal("123.4000")
        formatted = format_decimal(value, strip_zeros=False)
        self.assertEqual(formatted, "123.40000000")
        
        # Format decimal without trailing zeros
        formatted = format_decimal(value, strip_zeros=True)
        self.assertEqual(formatted, "123.4")
    
    def test_parse_decimal(self):
        """Test parsing decimal values."""
        # Parse string
        value = parse_decimal("123.45")
        self.assertEqual(value, Decimal("123.45"))
        
        # Parse integer
        value = parse_decimal(123)
        self.assertEqual(value, Decimal("123"))
        
        # Parse float
        value = parse_decimal(123.45)
        self.assertEqual(value, Decimal("123.45"))
        
        # Parse decimal
        original = Decimal("123.45")
        value = parse_decimal(original)
        self.assertEqual(value, original)


class TestDatetimeFunctions(unittest.TestCase):
    """Test cases for datetime functions."""

    def test_timestamp_conversions(self):
        """Test timestamp to datetime and back conversions."""
        # Get current timestamp
        now = int(time.time())
        
        # Convert to datetime
        dt = timestamp_to_datetime(now)
        
        # Convert back to timestamp
        timestamp = datetime_to_timestamp(dt)
        
        # Verify conversions
        self.assertEqual(timestamp, now)
    
    def test_datetime_formatting(self):
        """Test datetime formatting and parsing."""
        # Create datetime
        dt = datetime(2023, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        
        # Format datetime
        formatted = format_datetime(dt)
        self.assertEqual(formatted, "2023-01-15 12:30:45")
        
        # Format with custom format
        formatted = format_datetime(dt, "%Y/%m/%d %H:%M")
        self.assertEqual(formatted, "2023/01/15 12:30")
        
        # Parse datetime
        parsed = parse_datetime("2023-01-15 12:30:45")
        self.assertEqual(parsed.year, 2023)
        self.assertEqual(parsed.month, 1)
        self.assertEqual(parsed.day, 15)
        self.assertEqual(parsed.hour, 12)
        self.assertEqual(parsed.minute, 30)
        self.assertEqual(parsed.second, 45)
        
        # Parse with custom format
        parsed = parse_datetime("2023/01/15 12:30", "%Y/%m/%d %H:%M")
        self.assertEqual(parsed.year, 2023)
        self.assertEqual(parsed.month, 1)
        self.assertEqual(parsed.day, 15)
        self.assertEqual(parsed.hour, 12)
        self.assertEqual(parsed.minute, 30)


class TestJsonFunctions(unittest.TestCase):
    """Test cases for JSON functions."""

    def test_json_serialize(self):
        """Test JSON serialization."""
        # Create test object with various types
        obj = {
            "string": "test",
            "integer": 123,
            "float": 123.45,
            "decimal": Decimal("123.45"),
            "datetime": datetime(2023, 1, 15, 12, 30, 45),
            "list": [1, 2, 3],
            "set": {4, 5, 6},
            "nested": {
                "key": "value"
            }
        }
        
        # Serialize to JSON
        json_str = to_json(obj)
        
        # Verify serialization
        self.assertIsNotNone(json_str)
        
        # Parse JSON
        parsed = from_json(json_str)
        
        # Verify parsed object
        self.assertEqual(parsed["string"], "test")
        self.assertEqual(parsed["integer"], 123)
        self.assertEqual(parsed["float"], 123.45)
        self.assertEqual(parsed["decimal"], "123.45")  # Decimal converted to string
        self.assertTrue("datetime" in parsed)  # Datetime converted to ISO format
        self.assertEqual(parsed["list"], [1, 2, 3])
        self.assertEqual(set(parsed["set"]), {4, 5, 6})  # Set converted to list
        self.assertEqual(parsed["nested"]["key"], "value")
    
    def test_is_valid_json(self):
        """Test JSON validation."""
        # Valid JSON
        self.assertTrue(is_valid_json('{"key": "value"}'))
        self.assertTrue(is_valid_json('[1, 2, 3]'))
        
        # Invalid JSON
        self.assertFalse(is_valid_json('{"key": value}'))  # Missing quotes
        self.assertFalse(is_valid_json('[1, 2, 3'))  # Missing closing bracket


class TestMiscFunctions(unittest.TestCase):
    """Test cases for miscellaneous utility functions."""

    def test_safe_divide(self):
        """Test safe division."""
        # Normal division
        result = safe_divide(10, 2)
        self.assertEqual(result, 5)
        
        # Division by zero
        result = safe_divide(10, 0)
        self.assertEqual(result, Decimal("0"))
        
        # Division by zero with custom default
        result = safe_divide(10, 0, default=Decimal("999"))
        self.assertEqual(result, Decimal("999"))
    
    def test_truncate_string(self):
        """Test string truncation."""
        # String shorter than max length
        result = truncate_string("Hello", 10)
        self.assertEqual(result, "Hello")
        
        # String longer than max length
        result = truncate_string("Hello, world!", 10)
        self.assertEqual(result, "Hello, wo...")
        
        # String longer than max length with custom suffix
        result = truncate_string("Hello, world!", 10, suffix="[...]")
        self.assertEqual(result, "Hello[...]")
    
    def test_get_exception_traceback(self):
        """Test getting exception traceback."""
        try:
            # Raise an exception
            raise ValueError("Test error")
        except Exception as e:
            # Get traceback
            traceback = get_exception_traceback(e)
            
            # Verify traceback
            self.assertIsNotNone(traceback)
            self.assertIn("ValueError: Test error", traceback)
    
    def test_get_environment_variable(self):
        """Test getting environment variables."""
        # Set environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        # Get existing variable
        value = get_environment_variable("TEST_VAR")
        self.assertEqual(value, "test_value")
        
        # Get non-existent variable with default
        value = get_environment_variable("NON_EXISTENT_VAR", default="default_value")
        self.assertEqual(value, "default_value")
        
        # Get non-existent variable without default
        value = get_environment_variable("NON_EXISTENT_VAR")
        self.assertIsNone(value)
        
        # Get required non-existent variable
        with self.assertRaises(ValueError):
            get_environment_variable("NON_EXISTENT_VAR", required=True)
    
    def test_chunks(self):
        """Test splitting a list into chunks."""
        # Create test list
        test_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Split into chunks of size 3
        result = chunks(test_list, 3)
        
        # Verify chunks
        self.assertEqual(len(result), 4)
        self  3)
        
        # Verify chunks
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], [1, 2, 3])
        self.assertEqual(result[1], [4, 5, 6])
        self.assertEqual(result[2], [7, 8, 9])
        self.assertEqual(result[3], [10])
        
        # Split into chunks of size 5
        result = chunks(test_list, 5)
        
        # Verify chunks
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [1, 2, 3, 4, 5])
        self.assertEqual(result[1], [6, 7, 8, 9, 10])


if __name__ == '__main__':
    unittest.main()