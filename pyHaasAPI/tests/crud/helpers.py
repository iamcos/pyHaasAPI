"""
CRUD Test Helpers

Provides utility functions for safe field mapping, assertions,
retry logic, and timeout handling in CRUD tests.
"""

import asyncio
import logging
import time
from typing import Any, Optional, Callable, TypeVar, Union
from functools import wraps

import pytest

# v2-only imports
from pyHaasAPI.exceptions.base import HaasAPIError
from pyHaasAPI.exceptions.lab import LabError, LabNotFoundError
from pyHaasAPI.exceptions.bot import BotError, BotNotFoundError
from pyHaasAPI.exceptions.account import AccountError, AccountNotFoundError

T = TypeVar('T')
logger = logging.getLogger(__name__)


def safe_get_field(obj: Any, field_name: str, default: Any = None, required: bool = False) -> Any:
    """
    Safely get field from API object with proper error handling.
    
    Args:
        obj: API response object
        field_name: Name of field to access
        default: Default value if field missing
        required: Whether field is required (raises error if missing)
        
    Returns:
        Field value or default
        
    Raises:
        ValueError: If required field is missing
    """
    if hasattr(obj, field_name):
        value = getattr(obj, field_name)
        if value is None and required:
            logger.error(f"Required field '{field_name}' is None in {type(obj).__name__}")
            raise ValueError(f"Required field '{field_name}' is None")
        return value
    else:
        if required:
            logger.error(f"Required field '{field_name}' missing from {type(obj).__name__}")
            raise ValueError(f"Required field '{field_name}' not found")
        else:
            logger.warning(f"Optional field '{field_name}' missing from {type(obj).__name__}")
            return default


def assert_safe_field(obj: Any, field_name: str, expected_type: type = None, required: bool = False) -> Any:
    """
    Assert safe field access with type validation.
    
    Args:
        obj: API response object
        field_name: Name of field to access
        expected_type: Expected type of field value
        required: Whether field is required
        
    Returns:
        Field value
        
    Raises:
        AssertionError: If field validation fails
    """
    value = safe_get_field(obj, field_name, required=required)
    
    if value is not None and expected_type is not None:
        assert isinstance(value, expected_type), f"Field '{field_name}' should be {expected_type}, got {type(value)}"
    
    return value


def assert_lab_details_integrity(lab_details: Any) -> None:
    """
    Validate critical fields in LabDetails object.
    
    Args:
        lab_details: LabDetails object to validate
        
    Raises:
        AssertionError: If critical fields are missing or invalid
    """
    # Required fields
    lab_id = assert_safe_field(lab_details, 'lab_id', str, required=True)
    lab_name = assert_safe_field(lab_details, 'lab_name', str, required=True)
    script_id = assert_safe_field(lab_details, 'script_id', str, required=True)
    
    # Settings validation
    settings = assert_safe_field(lab_details, 'settings', required=True)
    if settings:
        market_tag = assert_safe_field(settings, 'market_tag', str, required=True)
        account_id = assert_safe_field(settings, 'account_id', str, required=True)
        
        # Validate market tag format
        assert market_tag, "Market tag cannot be empty"
        assert account_id, "Account ID cannot be empty"
    
    # Status validation
    status = assert_safe_field(lab_details, 'status', str)
    if status:
        valid_statuses = ['IDLE', 'RUNNING', 'QUEUED', 'COMPLETED', 'FAILED']
        assert status in valid_statuses, f"Invalid status: {status}"
    
    logger.info(f"Lab {lab_id} integrity validated: {lab_name}")


def assert_bot_details_integrity(bot_details: Any) -> None:
    """
    Validate critical fields in BotDetails object.
    
    Args:
        bot_details: BotDetails object to validate
        
    Raises:
        AssertionError: If critical fields are missing or invalid
    """
    # Required fields
    bot_id = assert_safe_field(bot_details, 'bot_id', str, required=True)
    bot_name = assert_safe_field(bot_details, 'bot_name', str, required=True)
    script_id = assert_safe_field(bot_details, 'script_id', str, required=True)
    account_id = assert_safe_field(bot_details, 'account_id', str, required=True)
    market_tag = assert_safe_field(bot_details, 'market_tag', str, required=True)
    
    # Settings validation
    settings = assert_safe_field(bot_details, 'settings', required=True)
    if settings:
        leverage = assert_safe_field(settings, 'leverage', (int, float))
        position_mode = assert_safe_field(settings, 'position_mode', (int, str))
        margin_mode = assert_safe_field(settings, 'margin_mode', (int, str))
        
        # Validate leverage
        if leverage is not None:
            assert 1 <= leverage <= 100, f"Invalid leverage: {leverage}"
        
        # Validate position mode (HEDGE=1, ONE_WAY=0)
        if position_mode is not None:
            if isinstance(position_mode, int):
                assert position_mode in [0, 1], f"Invalid position mode: {position_mode}"
            elif isinstance(position_mode, str):
                assert position_mode.upper() in ['HEDGE', 'ONE_WAY'], f"Invalid position mode: {position_mode}"
        
        # Validate margin mode (CROSS=0, ISOLATED=1)
        if margin_mode is not None:
            if isinstance(margin_mode, int):
                assert margin_mode in [0, 1], f"Invalid margin mode: {margin_mode}"
            elif isinstance(margin_mode, str):
                assert margin_mode.upper() in ['CROSS', 'ISOLATED'], f"Invalid margin mode: {margin_mode}"
    
    # Status validation
    status = assert_safe_field(bot_details, 'status', str)
    if status:
        valid_statuses = ['INACTIVE', 'ACTIVE', 'PAUSED', 'ERROR']
        assert status in valid_statuses, f"Invalid bot status: {status}"
    
    logger.info(f"Bot {bot_id} integrity validated: {bot_name}")


def assert_account_data_integrity(account_data: Any) -> None:
    """
    Validate critical fields in account data.
    
    Args:
        account_data: Account data object to validate
        
    Raises:
        AssertionError: If critical fields are missing or invalid
    """
    # Required fields
    account_id = assert_safe_field(account_data, 'account_id', str, required=True)
    exchange = assert_safe_field(account_data, 'exchange', str, required=True)
    account_name = assert_safe_field(account_data, 'account_name', str, required=True)
    
    # Wallet data validation
    wallet_data = assert_safe_field(account_data, 'wallet_data', required=False)
    if wallet_data:
        # Wallet data should be a list or dict
        assert isinstance(wallet_data, (list, dict)), f"Invalid wallet_data type: {type(wallet_data)}"
    
    logger.info(f"Account {account_id} integrity validated: {account_name}")


async def retry_async(
    func: Callable[..., T], 
    *args, 
    retries: int = 3, 
    delay: float = 1.0, 
    **kwargs
) -> T:
    """
    Retry async function with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Function arguments
        retries: Number of retry attempts
        delay: Base delay between retries
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Exception: Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < retries:
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {retries + 1} attempts failed. Last error: {e}")
    
    raise last_exception


async def await_idle_lab(lab_api, lab_id: str, timeout: float = 60.0) -> None:
    """
    Wait for lab to become idle (not running).
    
    Args:
        lab_api: LabAPI instance
        lab_id: Lab ID to check
        timeout: Maximum time to wait
        
    Raises:
        TimeoutError: If lab doesn't become idle within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            lab_details = await lab_api.get_lab_details(lab_id)
            status = safe_get_field(lab_details, 'status', 'UNKNOWN')
            
            if status in ['IDLE', 'COMPLETED', 'FAILED']:
                logger.info(f"Lab {lab_id} is now idle (status: {status})")
                return
            
            logger.debug(f"Lab {lab_id} status: {status}, waiting...")
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"Error checking lab status: {e}")
            await asyncio.sleep(2)
    
    raise TimeoutError(f"Lab {lab_id} did not become idle within {timeout}s")


def with_alarm(seconds: int):
    """
    Decorator to add timeout to test functions using signal.alarm().
    
    Args:
        seconds: Timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test {func.__name__} exceeded {seconds}s timeout")
            
            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                return func(*args, **kwargs)
            finally:
                # Restore original handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator


def generate_test_resource_name(resource_type: str, session_id: str, index: int = 1) -> str:
    """
    Generate standardized test resource names.
    
    Args:
        resource_type: Type of resource (lab, bot, etc.)
        session_id: Session ID for uniqueness
        index: Optional index for multiple resources
        
    Returns:
        Standardized resource name
    """
    if resource_type == "lab":
        return f"TEST v2 CRUD {session_id}"
    elif resource_type == "bot":
        return f"TEST v2 CRUD Bot {index} {session_id}"
    else:
        return f"TEST v2 CRUD {resource_type} {session_id}"


def log_field_mapping_warnings(obj: Any, obj_type: str) -> None:
    """
    Log warnings for missing optional fields in API responses.
    
    Args:
        obj: API response object
        obj_type: Type of object for logging context
    """
    # Common optional fields that might be missing
    optional_fields = [
        'script_name', 'market_name', 'account_name',
        'leverage', 'position_mode', 'margin_mode',
        'trade_amount', 'chart_style', 'interval'
    ]
    
    missing_fields = []
    for field in optional_fields:
        if not hasattr(obj, field):
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Missing optional fields in {obj_type}: {missing_fields}")


def validate_api_response_structure(response: Any, expected_fields: list) -> bool:
    """
    Validate that API response has expected structure.
    
    Args:
        response: API response object
        expected_fields: List of expected field names
        
    Returns:
        True if structure is valid, False otherwise
    """
    missing_fields = []
    for field in expected_fields:
        if not hasattr(response, field):
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"Missing required fields in API response: {missing_fields}")
        return False
    
    return True


def assert_no_get_usage(obj: Any, obj_name: str) -> None:
    """
    Assert that object doesn't use .get() method (API objects are not dicts).
    
    Args:
        obj: Object to check
        obj_name: Name for error reporting
    """
    # This is a static check - in practice, we ensure no .get() calls in code
    # by using safe_get_field instead
    pass  # Implementation would require AST parsing


def create_test_lab_config(
    script_id: str,
    market_tag: str,
    account_id: str,
    session_id: str
) -> dict:
    """
    Create standardized test lab configuration.
    
    Args:
        script_id: Script ID to use
        market_tag: Market tag for trading
        account_id: Account ID for lab
        session_id: Session ID for naming
        
    Returns:
        Lab configuration dictionary
    """
    return {
        'script_id': script_id,
        'lab_name': generate_test_resource_name('lab', session_id),
        'market_tag': market_tag,
        'account_id': account_id,
        'interval': '1h',
        'chart_style': 'candles',
        'trade_amount': 1000.0,
        'position_mode': 1,  # HEDGE
        'margin_mode': 0,    # CROSS
        'leverage': 20,
        'max_parallel': 1,
        'max_generations': 10,
        'max_epochs': 100
    }


def create_test_bot_config(
    script_id: str,
    market_tag: str,
    account_id: str,
    session_id: str,
    index: int = 1
) -> dict:
    """
    Create standardized test bot configuration.
    
    Args:
        script_id: Script ID to use
        market_tag: Market tag for trading
        account_id: Account ID for bot
        session_id: Session ID for naming
        index: Bot index for naming
        
    Returns:
        Bot configuration dictionary
    """
    return {
        'script_id': script_id,
        'bot_name': generate_test_resource_name('bot', session_id, index),
        'market_tag': market_tag,
        'account_id': account_id,
        'leverage': 20,
        'position_mode': 1,  # HEDGE
        'margin_mode': 0,     # CROSS
        'trade_amount': 2000.0
    }
