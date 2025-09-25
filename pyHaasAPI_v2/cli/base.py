"""
Base CLI Classes for pyHaasAPI v2

This module provides base classes for CLI tools using the new v2 architecture
with async support, type safety, and comprehensive error handling.
"""

import asyncio
import os
import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..core import (
    AsyncHaasClient, Settings,
    AsyncHaasClientWrapper, AsyncClientConfig, AsyncClientFactory,
    type_checked, strict_type_checked, lenient_type_checked,
    is_type_checking_enabled, get_type_config
)
from ..core.auth import AuthenticationManager
from ..config.api_config import APIConfig
from ..api import LabAPI, BotAPI, AccountAPI, ScriptAPI, MarketAPI, BacktestAPI, OrderAPI
from ..services import LabService, BotService, AnalysisService, ReportingService
from ..tools import DataDumper, TestingManager
from ..exceptions import APIError, AuthenticationError, ValidationError
from ..core.logging import get_logger

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class CLIConfig:
    """Configuration for CLI tools"""
    host: str = "127.0.0.1"
    port: int = 8090
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    enable_caching: bool = True
    cache_ttl: float = 300.0
    enable_rate_limiting: bool = True
    max_concurrent_requests: int = 10
    log_level: str = "INFO"
    strict_mode: bool = False


class BaseCLI(ABC):
    """
    Base class for all CLI tools with async support and type safety.
    
    Provides common functionality including authentication, configuration,
    logging, and error handling for all CLI tools.
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self.logger = get_logger(self.__class__.__name__)
        
        # Core components
        self.client: Optional[AsyncHaasClient] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.async_client: Optional[AsyncHaasClientWrapper] = None
        
        # API modules
        self.lab_api: Optional[LabAPI] = None
        self.bot_api: Optional[BotAPI] = None
        self.account_api: Optional[AccountAPI] = None
        self.script_api: Optional[ScriptAPI] = None
        self.market_api: Optional[MarketAPI] = None
        self.backtest_api: Optional[BacktestAPI] = None
        self.order_api: Optional[OrderAPI] = None
        
        # Services
        self.lab_service: Optional[LabService] = None
        self.bot_service: Optional[BotService] = None
        self.analysis_service: Optional[AnalysisService] = None
        self.reporting_service: Optional[ReportingService] = None
        
        # Tools
        self.data_dumper: Optional[DataDumper] = None
        self.testing_manager: Optional[TestingManager] = None
        
        # Setup
        self._setup_logging()
        self._setup_type_checking()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_type_checking(self) -> None:
        """Setup type checking configuration"""
        if is_type_checking_enabled():
            type_config = get_type_config()
            type_config.strict_mode = self.config.strict_mode
            type_config.log_validation_errors = True

    @strict_type_checked
    async def connect(self) -> bool:
        """
        Connect to the HaasOnline API with authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Get credentials from environment
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                self.logger.error("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Build API config for v2 client
            api_config = APIConfig(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
                email=email,
                password=password
            )
            
            # Create client and auth manager
            self.client = AsyncHaasClient(api_config)
            self.auth_manager = AuthenticationManager(self.client, api_config)
            
            # Authenticate (uses config credentials)
            await self.auth_manager.authenticate()
            
            # Create async client wrapper
            async_config = AsyncClientConfig(
                cache_ttl=self.config.cache_ttl,
                enable_caching=self.config.enable_caching,
                enable_rate_limiting=self.config.enable_rate_limiting,
                max_concurrent_requests=self.config.max_concurrent_requests,
                request_timeout=self.config.timeout
            )
            
            self.async_client = AsyncHaasClientWrapper(
                self.client, self.auth_manager, async_config
            )
            
            # Initialize API modules
            await self._initialize_api_modules()
            
            # Initialize services
            await self._initialize_services()
            
            # Initialize tools
            await self._initialize_tools()
            
            self.logger.info("Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to HaasOnline API: {e}")
            # Default behavior: stop execution when server authentication fails
            if "authentication" in str(e).lower() or "html" in str(e).lower() or "missing user data" in str(e).lower():
                self.logger.error("Server authentication issue detected. Stopping execution.")
                raise SystemExit(1)
            return False

    async def _initialize_api_modules(self) -> None:
        """Initialize API modules"""
        if not self.async_client:
            raise RuntimeError("Async client not initialized")
        
        self.lab_api = LabAPI(self.async_client)
        self.bot_api = BotAPI(self.async_client)
        self.account_api = AccountAPI(self.async_client)
        self.script_api = ScriptAPI(self.async_client)
        self.market_api = MarketAPI(self.async_client)
        self.backtest_api = BacktestAPI(self.async_client)
        self.order_api = OrderAPI(self.async_client)

    async def _initialize_services(self) -> None:
        """Initialize services"""
        if not self.async_client:
            raise RuntimeError("Async client not initialized")
        
        # Initialize services with proper dependencies
        self.lab_service = LabService(
            self.lab_api, self.backtest_api, self.script_api, self.account_api
        )
        self.bot_service = BotService(
            self.bot_api, self.account_api, self.backtest_api, self.market_api,
            self.client, self.auth_manager
        )
        self.analysis_service = AnalysisService(
            self.lab_api, self.backtest_api, self.bot_api,
            self.client, self.auth_manager
        )
        self.reporting_service = ReportingService()

    async def _initialize_tools(self) -> None:
        """Initialize tools"""
        if not self.async_client:
            raise RuntimeError("Async client not initialized")
        
        self.data_dumper = DataDumper(self.async_client)
        self.testing_manager = TestingManager(self.async_client)

    @strict_type_checked
    async def disconnect(self) -> None:
        """Disconnect from the API and cleanup resources"""
        try:
            if self.async_client:
                await self.async_client.__aexit__(None, None, None)
            
            if self.auth_manager:
                await self.auth_manager.logout()
            
            self.logger.info("Disconnected from HaasOnline API")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    @strict_type_checked
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "status": "healthy",
            "timestamp": None,
            "components": {}
        }
        
        try:
            if self.async_client:
                health_status["components"]["async_client"] = await self.async_client.health_check()
            
            if self.lab_api:
                # Simple health check - try to get labs
                await self.lab_api.get_labs()
                health_status["components"]["lab_api"] = "healthy"
            
            health_status["timestamp"] = asyncio.get_event_loop().time()
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status

    @abstractmethod
    async def run(self, args: List[str]) -> int:
        """
        Run the CLI tool with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass

    @strict_type_checked
    async def execute_with_error_handling(self, func: callable, *args, **kwargs) -> Any:
        """
        Execute a function with comprehensive error handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            APIError: If API operation fails
            ValidationError: If validation fails
            Exception: For other errors
        """
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            self.logger.error(f"API Error: {e}")
            raise
        except ValidationError as e:
            self.logger.error(f"Validation Error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected Error: {e}")
            raise

    @strict_type_checked
    def create_parser(self, description: str) -> Any:
        """
        Create argument parser with common options.
        
        Args:
            description: Parser description
            
        Returns:
            ArgumentParser instance
        """
        import argparse
        
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Common options
        parser.add_argument(
            '--host', 
            default=self.config.host,
            help='API host (default: 127.0.0.1)'
        )
        parser.add_argument(
            '--port', 
            type=int, 
            default=self.config.port,
            help='API port (default: 8090)'
        )
        parser.add_argument(
            '--timeout', 
            type=float, 
            default=self.config.timeout,
            help='Request timeout in seconds (default: 30.0)'
        )
        parser.add_argument(
            '--log-level', 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default=self.config.log_level,
            help='Log level (default: INFO)'
        )
        parser.add_argument(
            '--strict-mode', 
            action='store_true',
            help='Enable strict mode for type checking'
        )
        parser.add_argument(
            '--dry-run', 
            action='store_true',
            help='Perform a dry run without making changes'
        )
        parser.add_argument(
            '--verbose', '-v', 
            action='store_true',
            help='Enable verbose output'
        )
        
        return parser

    @strict_type_checked
    def update_config_from_args(self, args: Any) -> None:
        """
        Update configuration from parsed arguments.
        
        Args:
            args: Parsed arguments
        """
        if hasattr(args, 'host'):
            self.config.host = args.host
        if hasattr(args, 'port'):
            self.config.port = args.port
        if hasattr(args, 'timeout'):
            self.config.timeout = args.timeout
        if hasattr(args, 'log_level'):
            self.config.log_level = args.log_level
        if hasattr(args, 'strict_mode'):
            self.config.strict_mode = args.strict_mode

    @strict_type_checked
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    @strict_type_checked
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class AsyncBaseCLI(BaseCLI):
    """
    Async base class for CLI tools that require async operations.
    
    Provides additional async-specific functionality and utilities.
    """

    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config)
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

    @strict_type_checked
    async def run_async(self, func: callable, *args, **kwargs) -> Any:
        """
        Run an async function with proper event loop handling.
        
        Args:
            func: Async function to run
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in async operation: {e}")
            raise

    @strict_type_checked
    def run_sync(self, func: callable, *args, **kwargs) -> Any:
        """
        Run a sync function in the event loop.
        
        Args:
            func: Sync function to run
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, func, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in sync operation: {e}")
            raise

    @strict_type_checked
    async def run_concurrent(self, tasks: List[callable], max_concurrent: int = 10) -> List[Any]:
        """
        Run multiple tasks concurrently with concurrency control.
        
        Args:
            tasks: List of async functions to run
            max_concurrent: Maximum concurrent tasks
            
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task()
        
        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

    @strict_type_checked
    async def run_with_progress(self, tasks: List[callable], description: str = "Processing") -> List[Any]:
        """
        Run tasks with progress tracking.
        
        Args:
            tasks: List of async functions to run
            description: Progress description
            
        Returns:
            List of results
        """
        results = []
        total = len(tasks)
        
        self.logger.info(f"{description}: Starting {total} tasks")
        
        for i, task in enumerate(tasks):
            try:
                result = await task()
                results.append(result)
                self.logger.info(f"{description}: Completed {i+1}/{total}")
            except Exception as e:
                self.logger.error(f"{description}: Failed task {i+1}/{total}: {e}")
                results.append(None)
        
        self.logger.info(f"{description}: Completed {len(results)}/{total} tasks")
        return results
