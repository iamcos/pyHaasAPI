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
try:
    from ..api.order.order_api import OrderAPI
except ImportError:
    OrderAPI = None
try:
    from ..services.lab.lab_service import LabService
except ImportError:
    LabService = None
try:
    from ..services.bot.bot_service import BotService
except ImportError:
    BotService = None
try:
    from ..services.analysis.analysis_service import AnalysisService
except ImportError:
    AnalysisService = None
try:
    from ..services.reporting.reporting_service import ReportingService
except ImportError:
    ReportingService = None
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
    
    def __post_init__(self):
        """Set log_level if not provided"""
        if not hasattr(self, 'log_level') or not self.log_level:
            self.log_level = "INFO"


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
        
        # Managers
        self.server_manager: Optional[ServerManager] = None
        self.server_content_manager: Optional[ServerContentManager] = None
        self.account_manager: Optional[AccountManager] = None
        self.bot_manager: Optional[BotManager] = None
        self.sync_history_manager: Optional[SyncHistoryManager] = None
        self.lab_clone_manager: Optional[LabCloneManager] = None
        self.lab_config_manager: Optional[LabConfigManager] = None
        self.backtesting_manager: Optional[BacktestingManager] = None
        
        # Settings (for managers that need it)
        self.settings: Optional[Settings] = None
        
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
            
            # Initialize managers
            await self._initialize_managers()
            
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
    
    async def _initialize_managers(self) -> None:
        """Initialize managers"""
        if not self.client or not self.auth_manager:
            raise RuntimeError("Client and auth manager not initialized")
        
        # Import managers
        from ...core.server_manager import ServerManager
        from ...services.server_content_manager import ServerContentManager
        from ...services.account_manager import AccountManager
        from ...services.bot_manager import BotManager
        from ...services.sync_history_manager import SyncHistoryManager
        from ...services.lab_clone_manager import LabCloneManager
        from ...services.lab_config_manager import LabConfigManager
        from ...core.backtesting_manager import BacktestingManager
        from ...config.settings import Settings
        
        # Initialize settings
        self.settings = Settings()
        
        # Initialize ServerManager
        self.server_manager = ServerManager(self.settings)
        
        # Initialize ServerContentManager (needs server name - use default)
        self.server_content_manager = ServerContentManager(
            server=self.settings.default_server,
            lab_api=self.lab_api,
            bot_api=self.bot_api,
            backtest_api=self.backtest_api,
            account_api=self.account_api
        )
        
        # Initialize AccountManager
        self.account_manager = AccountManager(
            account_api=self.account_api,
            server=self.settings.default_server
        )
        
        # Initialize BotManager
        self.bot_manager = BotManager(bot_service=self.bot_service)
        
        # Initialize SyncHistoryManager
        self.sync_history_manager = SyncHistoryManager(
            market_api=self.market_api,
            backtest_api=self.backtest_api,
            client=self.client,
            auth_manager=self.auth_manager
        )
        
        # Initialize LabCloneManager
        self.lab_clone_manager = LabCloneManager(
            lab_api=self.lab_api,
            client=self.client,
            auth_manager=self.auth_manager
        )
        
        # Initialize LabConfigManager
        self.lab_config_manager = LabConfigManager(
            lab_api=self.lab_api,
            market_api=self.market_api,
            client=self.client,
            auth_manager=self.auth_manager
        )
        
        # Initialize BacktestingManager
        self.backtesting_manager = BacktestingManager(
            client=self.client,
            auth_manager=self.auth_manager,
            server_manager=self.server_manager
        )

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

    # Utility methods for common patterns

    @staticmethod
    def safe_get(obj: Any, field: str, default: Any = None) -> Any:
        """
        Safely get a field from an object or dictionary.
        
        Args:
            obj: Object or dictionary
            field: Field name to get
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)

    @staticmethod
    def safe_has(obj: Any, field: str) -> bool:
        """
        Safely check if an object or dictionary has a field.
        
        Args:
            obj: Object or dictionary
            field: Field name to check
            
        Returns:
            True if field exists, False otherwise
        """
        if isinstance(obj, dict):
            return field in obj
        return hasattr(obj, field)

    def format_output(
        self,
        data: List[Any],
        format_type: str,
        output_file: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Format and output data in JSON, CSV, or table format.
        
        Args:
            data: List of data objects/dictionaries to format
            format_type: Output format ('json', 'csv', or 'table')
            output_file: Optional output file path
            field_mapping: Optional mapping of field names for CSV/table headers
        """
        if format_type == 'json':
            import json
            # Convert objects to dicts if needed
            json_data = [
                item if isinstance(item, dict) else item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else vars(item)
                for item in data
            ]
            output = json.dumps(json_data, indent=2, default=str)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
            else:
                print(output)
                
        elif format_type == 'csv':
            import csv
            
            if not data:
                return
                
            # Get fieldnames from first item
            first_item = data[0]
            if isinstance(first_item, dict):
                fieldnames = list(first_item.keys())
            elif hasattr(first_item, 'model_dump'):
                fieldnames = list(first_item.model_dump().keys())
            elif hasattr(first_item, 'dict'):
                fieldnames = list(first_item.dict().keys())
            else:
                fieldnames = list(vars(first_item).keys())
            
            # Apply field mapping if provided
            if field_mapping:
                fieldnames = [field_mapping.get(f, f) for f in fieldnames]
            
            # Convert items to dicts
            rows = []
            for item in data:
                if isinstance(item, dict):
                    rows.append(item)
                elif hasattr(item, 'model_dump'):
                    rows.append(item.model_dump())
                elif hasattr(item, 'dict'):
                    rows.append(item.dict())
                else:
                    rows.append(vars(item))
            
            if output_file:
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            else:
                # Print CSV to stdout
                print(','.join(fieldnames))
                for row in rows:
                    print(','.join(str(row.get(f, '')) for f in fieldnames))
                    
        else:  # table format
            if not data:
                return
                
            # Get fieldnames from first item
            first_item = data[0]
            if isinstance(first_item, dict):
                fieldnames = list(first_item.keys())
            elif hasattr(first_item, 'model_dump'):
                fieldnames = list(first_item.model_dump().keys())
            elif hasattr(first_item, 'dict'):
                fieldnames = list(first_item.dict().keys())
            else:
                fieldnames = list(vars(first_item).keys())
            
            # Apply field mapping if provided
            if field_mapping:
                fieldnames = [field_mapping.get(f, f) for f in fieldnames]
            
            # Calculate column widths
            col_widths = {f: len(f) for f in fieldnames}
            for item in data:
                if isinstance(item, dict):
                    item_dict = item
                elif hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                elif hasattr(item, 'dict'):
                    item_dict = item.dict()
                else:
                    item_dict = vars(item)
                    
                for field in fieldnames:
                    value = str(item_dict.get(field, ''))[:50]  # Truncate long values
                    col_widths[field] = max(col_widths[field], len(value))
            
            # Print header
            header = ' | '.join(f"{f:<{col_widths[f]}}" for f in fieldnames)
            print(header)
            print('-' * len(header))
            
            # Print rows
            for item in data:
                if isinstance(item, dict):
                    item_dict = item
                elif hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                elif hasattr(item, 'dict'):
                    item_dict = item.dict()
                else:
                    item_dict = vars(item)
                    
                row = ' | '.join(
                    f"{str(item_dict.get(f, ''))[:50]:<{col_widths[f]}}"
                    for f in fieldnames
                )
                print(row)

    def check_status_enum(
        self,
        status_value: Any,
        enum_class: type,
        target_status: str
    ) -> bool:
        """
        Check if a status value matches an enum status.
        
        Args:
            status_value: Status value to check (int, str, or enum)
            enum_class: Enum class to check against
            target_status: Name of target status in enum
            
        Returns:
            True if status matches, False otherwise
        """
        if not hasattr(enum_class, target_status):
            return False
            
        target_enum_value = getattr(enum_class, target_status).value
        
        # Handle different status_value types
        if isinstance(status_value, enum_class):
            return status_value.value == target_enum_value
        elif isinstance(status_value, int):
            return status_value == target_enum_value
        elif isinstance(status_value, str):
            # Try to match by name or value
            try:
                return enum_class[status_value.upper()].value == target_enum_value
            except (KeyError, AttributeError):
                return False
        return False

    def filter_by_status(
        self,
        items: List[Any],
        status_field: str,
        target_status: str,
        enum_class: Optional[type] = None
    ) -> List[Any]:
        """
        Filter items by status using enum comparison.
        
        Args:
            items: List of items to filter
            status_field: Field name containing status
            target_status: Target status name (enum name or string)
            enum_class: Optional enum class for status comparison
            
        Returns:
            Filtered list of items
        """
        if not enum_class:
            # Simple string comparison
            return [
                item for item in items
                if self.safe_get(item, status_field, '').lower() == target_status.lower()
            ]
        
        return [
            item for item in items
            if self.check_status_enum(
                self.safe_get(item, status_field),
                enum_class,
                target_status
            )
        ]