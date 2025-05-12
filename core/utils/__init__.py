#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Core Utilities Module
Author: ECLIPSEMOON
"""

import os
import sys
import logging
import json
import time
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any, Callable, TypeVar, Generic

# Setup logger
logger = logging.getLogger("core.utils")

# Type variable for generic functions
T = TypeVar('T')


class Result(Generic[T]):
    """Class representing the result of an operation."""
    
    def __init__(
        self,
        success: bool,
        value: Optional[T] = None,
        error: Optional[Exception] = None,
        message: Optional[str] = None,
    ):
        """
        Initialize the result.
        
        Args:
            success: Whether the operation was successful
            value: Value returned by the operation (if successful)
            error: Error that occurred during the operation (if unsuccessful)
            message: Message describing the result
        """
        self.success = success
        self.value = value
        self.error = error
        self.message = message
    
    @classmethod
    def ok(cls, value: Optional[T] = None, message: Optional[str] = None) -> 'Result[T]':
        """
        Create a successful result.
        
        Args:
            value: Value returned by the operation
            message: Message describing the result
            
        Returns:
            Result[T]: Successful result
        """
        return cls(True, value, None, message)
    
    @classmethod
    def err(cls, error: Optional[Exception] = None, message: Optional[str] = None) -> 'Result[T]':
        """
        Create an unsuccessful result.
        
        Args:
            error: Error that occurred during the operation
            message: Message describing the result
            
        Returns:
            Result[T]: Unsuccessful result
        """
        return cls(False, None, error, message)
    
    def __bool__(self) -> bool:
        """
        Convert to boolean.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.success


class Timer:
    """Class for measuring execution time."""
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the timer.
        
        Args:
            name: Name of the timer (for logging)
        """
        self.name = name or "Timer"
        self.start_time = None
        self.end_time = None
    
    def __enter__(self) -> 'Timer':
        """
        Start the timer.
        
        Returns:
            Timer: Self
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer."""
        self.stop()
    
    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self) -> float:
        """
        Stop the timer.
        
        Returns:
            float: Elapsed time in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        
        logger.info(f"{self.name}: {elapsed:.6f} seconds")
        
        return elapsed
    
    def elapsed(self) -> float:
        """
        Get the elapsed time.
        
        Returns:
            float: Elapsed time in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        if self.end_time is None:
            return time.time() - self.start_time
        else:
            return self.end_time - self.start_time


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Set up logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, log to console only)
        log_format: Log format (if None, use default)
    """
    # Convert log level string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Set up log format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure logging
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    logger.info(f"Logging configured with level {log_level}")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retrying a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (in seconds)
        backoff_factor: Factor to multiply delay by after each attempt
        exceptions: Exceptions to catch and retry on
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {str(e)}, retrying in {current_delay} seconds")
                    time.sleep(current_delay)
                    
                    attempt += 1
                    current_delay *= backoff_factor
        
        return wrapper
    
    return decorator


def format_decimal(
    value: Decimal,
    precision: int = 8,
    strip_zeros: bool = True,
) -> str:
    """
    Format a decimal value.
    
    Args:
        value: Decimal value to format
        precision: Number of decimal places
        strip_zeros: Whether to strip trailing zeros
        
    Returns:
        str: Formatted decimal value
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Format with specified precision
    formatted = f"{value:.{precision}f}"
    
    # Strip trailing zeros if requested
    if strip_zeros and '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    
    return formatted


def parse_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Parse a value as a decimal.
    
    Args:
        value: Value to parse
        
    Returns:
        Decimal: Parsed decimal value
    """
    if isinstance(value, Decimal):
        return value
    
    return Decimal(str(value))


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert a Unix timestamp to a datetime.
    
    Args:
        timestamp: Unix timestamp (in seconds)
        
    Returns:
        datetime: Datetime object
    """
    return datetime.fromtimestamp(timestamp, timezone.utc)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert a datetime to a Unix timestamp.
    
    Args:
        dt: Datetime object
        
    Returns:
        int: Unix timestamp (in seconds)
    """
    return int(dt.timestamp())


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    Format a datetime.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        str: Formatted datetime
    """
    return dt.strftime(format_str)


def parse_datetime(
    datetime_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> datetime:
    """
    Parse a datetime string.
    
    Args:
        datetime_str: Datetime string
        format_str: Format string
        
    Returns:
        datetime: Parsed datetime object
    """
    return datetime.strptime(datetime_str, format_str)


def json_serialize(obj: Any) -> Any:
    """
    Serialize an object to JSON.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Any: JSON-serializable object
    """
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)


def to_json(obj: Any, indent: Optional[int] = None) -> str:
    """
    Convert an object to a JSON string.
    
    Args:
        obj: Object to convert
        indent: Indentation level (if None, no indentation)
        
    Returns:
        str: JSON string
    """
    return json.dumps(obj, default=json_serialize, indent=indent)


def from_json(json_str: str) -> Any:
    """
    Parse a JSON string.
    
    Args:
        json_str: JSON string
        
    Returns:
        Any: Parsed object
    """
    return json.loads(json_str)


def safe_divide(
    numerator: Union[int, float, Decimal],
    denominator: Union[int, float, Decimal],
    default: Union[int, float, Decimal] = Decimal("0"),
) -> Union[int, float, Decimal]:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value to return if denominator is zero
        
    Returns:
        Union[int, float, Decimal]: Result of division or default value
    """
    if denominator == 0:
        return default
    
    return numerator / denominator


def truncate_string(
    s: str,
    max_length: int,
    suffix: str = "...",
) -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated string
    """
    if len(s) <= max_length:
        return s
    
    return s[:max_length - len(suffix)] + suffix


def get_exception_traceback(exception: Exception) -> str:
    """
    Get the traceback of an exception as a string.
    
    Args:
        exception: Exception to get traceback for
        
    Returns:
        str: Traceback as a string
    """
    return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))


def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_str: String to check
        
    Returns:
        bool: True if valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def get_environment_variable(
    name: str,
    default: Optional[str] = None,
    required: bool = False,
) -> Optional[str]:
    """
    Get an environment variable.
    
    Args:
        name: Name of the environment variable
        default: Default value if not found
        required: Whether the environment variable is required
        
    Returns:
        Optional[str]: Value of the environment variable or default
        
    Raises:
        ValueError: If the environment variable is required but not found
    """
    value = os.environ.get(name, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable {name} not found")
    
    return value


def chunks(lst: List[T], n: int) -> List[List[T]]:
    """
    Split a list into chunks of size n.
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List[List[T]]: List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


# Example usage
if __name__ == "__main__":
    # Set up logging
    setup_logging(log_level="INFO")
    
    # Example of using the Timer class
    with Timer("Example operation") as timer:
        # Simulate some work
        time.sleep(1)
    
    # Example of using the retry decorator
    @retry(max_attempts=3, delay=0.1)
    def example_function():
        # Simulate a failure
        if random.random() < 0.7:
            raise ValueError("Random failure")
        return "Success"
    
    try:
        result = example_function()
        print(f"Result: {result}")
    except ValueError:
        print("Function failed after retries")
    
    # Example of using the Result class
    def divide(a, b):
        try:
            return Result.ok(a / b, f"Successfully divided {a} by {b}")
        except ZeroDivisionError as e:
            return Result.err(e, "Cannot divide by zero")
    
    result1 = divide(10, 2)
    result2 = divide(10, 0)
    
    if result1:
        print(f"Result 1: {result1.value} - {result1.message}")
    else:
        print(f"Result 1 error: {result1.message}")
    
    if result2:
        print(f"Result 2: {result2.value} - {result2.message}")
    else:
        print(f"Result 2 error: {result2.message}")
    
    # Example of using other utility functions
    now = datetime.now()
    timestamp = datetime_to_timestamp(now)
    dt = timestamp_to_datetime(timestamp)
    
    print(f"Now: {now}")
    print(f"Timestamp: {timestamp}")
    print(f"Datetime from timestamp: {dt}")
    print(f"Formatted datetime: {format_datetime(now)}")
    
    # Example of JSON serialization
    data = {
        "name": "Example",
        "value": Decimal("123.456"),
        "timestamp": now,
        "items": [1, 2, 3],
        "set": {4, 5, 6}
    }
    
    json_str = to_json(data, indent=2)
    print(f"JSON: {json_str}")
    
    parsed_data = from_json(json_str)
    print(f"Parsed data: {parsed_data}")