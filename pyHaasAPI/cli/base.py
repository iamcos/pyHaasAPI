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

from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from ..config.api_config import APIConfig
from ..api.lab.lab_api import LabAPI
from ..api.bot.bot_api import BotAPI
from ..api.account.account_api import AccountAPI
from ..api.script.script_api import ScriptAPI
from ..api.market.market_api import MarketAPI
from ..api.backtest.backtest_api import BacktestAPI
from ..api.order.order_api import OrderAPI
from ..services.lab.lab_service import LabService
from ..services.bot.bot_service import BotService
from ..services.analysis.analysis_service import AnalysisService
from ..services.reporting.reporting_service import ReportingService
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
        
        # Setup
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

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
            
            # Preflight TCP reachability check for mandated tunnel
            try:
                async def _probe(port: int) -> bool:
                    try:
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection('127.0.0.1', port),
                            timeout=2.0
                        )
                        writer.close()
                        await writer.wait_closed()
                        return True
                    except Exception:
                        return False
                ok = await _probe(8090)
                if not ok:
                    raise ConnectionError(
                        "Tunnel preflight failed. Start the mandated SSH tunnel: "
                        "ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv0*"
                    )
            except Exception as e:
                self.logger.error(str(e))
                raise SystemExit(2)

            # Build API config for v2 client
            api_config = APIConfig(
                timeout=self.config.timeout,
                email=email,
                password=password
            )
            
            # Create client and auth manager
            self.client = AsyncHaasClient(api_config)
            self.auth_manager = AuthenticationManager(self.client, api_config)
            
            # Authenticate
            await self.auth_manager.authenticate()
            
            # Initialize API modules
            await self._initialize_api_modules()
            
            # Initialize services
            await self._initialize_services()
            
            self.logger.info("Successfully connected to HaasOnline API")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to HaasOnline API: {e}")
            if "authentication" in str(e).lower() or "html" in str(e).lower():
                self.logger.error("Server authentication issue detected. Stopping execution.")
                raise SystemExit(1)
            return False

    async def _initialize_api_modules(self) -> None:
        """Initialize API modules"""
        if not self.client or not self.auth_manager:
            raise RuntimeError("Client and auth manager not initialized")
        
        self.lab_api = LabAPI(self.client, self.auth_manager)
        self.bot_api = BotAPI(self.client, self.auth_manager)
        self.account_api = AccountAPI(self.client, self.auth_manager)
        self.script_api = ScriptAPI(self.client, self.auth_manager)
        self.market_api = MarketAPI(self.client, self.auth_manager)
        self.backtest_api = BacktestAPI(self.client, self.auth_manager)
        self.order_api = OrderAPI(self.client, self.auth_manager)

    async def _initialize_services(self) -> None:
        """Initialize services"""
        if not self.client or not self.auth_manager:
            raise RuntimeError("Client and auth manager not initialized")
        
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

    async def disconnect(self) -> None:
        """Disconnect from the API and cleanup resources"""
        try:
            if self.auth_manager:
                await self.auth_manager.logout()
            
            self.logger.info("Disconnected from HaasOnline API")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "status": "healthy",
            "timestamp": None,
            "components": {}
        }
        
        try:
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

    def update_config_from_args(self, args: Any) -> None:
        """
        Update configuration from parsed arguments.
        
        Args:
            args: Parsed arguments
        """
        if hasattr(args, 'timeout'):
            self.config.timeout = args.timeout
        if hasattr(args, 'log_level'):
            self.config.log_level = args.log_level
        if hasattr(args, 'strict_mode'):
            self.config.strict_mode = args.strict_mode

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()