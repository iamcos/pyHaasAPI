"""
HaasOnline API client with authentication, connection pooling, and retry logic.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin, urlencode
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.haasonline_config import HaasOnlineConfig
from .request_models import *
from .response_models import *


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_second: int, burst_limit: int):
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token for making a request."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_limit,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now
            
            if self.tokens < 1:
                # Wait until we have a token
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class HaasOnlineAPIError(Exception):
    """Base exception for HaasOnline API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(HaasOnlineAPIError):
    """Authentication-related errors."""
    pass


class RateLimitError(HaasOnlineAPIError):
    """Rate limiting errors."""
    pass


class ValidationError(HaasOnlineAPIError):
    """Request validation errors."""
    pass


class HaasOnlineClient:
    """
    HaasOnline API client with authentication, connection pooling, and retry logic.
    
    This client provides a robust interface to the HaasOnline API with:
    - Automatic authentication and session management
    - Connection pooling for efficient resource usage
    - Retry logic with exponential backoff
    - Rate limiting to respect API limits
    - Comprehensive error handling
    """
    
    def __init__(self, config: HaasOnlineConfig):
        """
        Initialize the HaasOnline API client.
        
        Args:
            config: HaasOnline configuration object
        """
        self.config = config
        self.session: Optional[requests.Session] = None
        self.async_session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(
            config.rate_limit.requests_per_second,
            config.rate_limit.burst_limit
        )
        
        # Authentication state
        self._authenticated = False
        self._auth_token: Optional[str] = None
        self._auth_expires: Optional[datetime] = None
        self._user_id: Optional[str] = None
        self._interface_key: Optional[str] = None
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def __enter__(self):
        """Context manager entry."""
        self._setup_session()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_async_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
    
    def _setup_session(self) -> None:
        """Setup synchronous HTTP session with connection pooling and retry logic."""
        if self.session is not None:
            return
            
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=self.config.connection.max_retries,
            backoff_factor=self.config.rate_limit.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Setup HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=self.config.connection.connection_pool_size,
            pool_maxsize=self.config.connection.connection_pool_size,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update(self.config.get_auth_headers())
        
        # Set timeout
        self.session.timeout = self.config.connection.timeout_seconds
        
        self.logger.info("HTTP session initialized with connection pooling")
    
    async def _setup_async_session(self) -> None:
        """Setup asynchronous HTTP session."""
        if self.async_session is not None:
            return
            
        connector = aiohttp.TCPConnector(
            limit=self.config.connection.connection_pool_size,
            limit_per_host=self.config.connection.connection_pool_size,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.connection.timeout_seconds)
        
        self.async_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.get_auth_headers()
        )
        
        self.logger.info("Async HTTP session initialized")
    
    def close(self) -> None:
        """Close synchronous session."""
        if self.session:
            self.session.close()
            self.session = None
            self.logger.info("HTTP session closed")
    
    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self.async_session:
            await self.async_session.close()
            self.async_session = None
            self.logger.info("Async HTTP session closed")
    
    def authenticate(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Authenticate with HaasOnline server.
        
        Args:
            username: Optional username override
            password: Optional password override
            
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.session:
            self._setup_session()
        
        auth_username = username or self.config.username
        auth_password = password or self.config.password
        
        if not auth_username or not auth_password:
            # Try API key authentication
            return self._authenticate_with_api_key()
        
        return self._authenticate_with_credentials(auth_username, auth_password)
    
    def _authenticate_with_api_key(self) -> bool:
        """Authenticate using API key and secret."""
        try:
            # Generate interface key
            self._interface_key = self._generate_interface_key()
            
            # Test API key authentication
            response = self._make_request(
                "GET",
                self.config.get_api_url("User"),
                params={
                    "channel": "GET_USER_INFO",
                    "interfacekey": self._interface_key
                }
            )
            
            if response.get("Success"):
                self._authenticated = True
                self._user_id = response.get("Data", {}).get("UserId")
                self.logger.info("Successfully authenticated with API key")
                return True
            else:
                raise AuthenticationError(f"API key authentication failed: {response.get('Error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"API key authentication failed: {e}")
            raise AuthenticationError(f"API key authentication failed: {e}")
    
    def _authenticate_with_credentials(self, username: str, password: str) -> bool:
        """Authenticate using username and password."""
        try:
            # Generate interface key
            self._interface_key = self._generate_interface_key()
            
            # Step 1: Login with credentials
            response = self._make_request(
                "POST",
                self.config.get_api_url("User"),
                data={
                    "channel": "LOGIN_WITH_CREDENTIALS",
                    "email": username,
                    "password": password,
                    "interfaceKey": self._interface_key
                }
            )
            
            if not response.get("Success"):
                raise AuthenticationError(f"Credential login failed: {response.get('Error', 'Unknown error')}")
            
            # Step 2: Complete authentication with one-time code
            # In production, this would require actual 2FA code
            # For now, we'll use a dummy code or skip this step
            response = self._make_request(
                "POST",
                self.config.get_api_url("User"),
                data={
                    "channel": "LOGIN_WITH_ONE_TIME_CODE",
                    "email": username,
                    "pincode": "123456",  # This would be actual 2FA code
                    "interfaceKey": self._interface_key
                }
            )
            
            if response.get("Success") and response.get("Data"):
                self._authenticated = True
                self._user_id = response["Data"].get("UserId")
                self.logger.info(f"Successfully authenticated user: {username}")
                return True
            else:
                raise AuthenticationError(f"2FA authentication failed: {response.get('Error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Credential authentication failed: {e}")
            raise AuthenticationError(f"Credential authentication failed: {e}")
    
    def _generate_interface_key(self) -> str:
        """Generate a unique interface key for the session."""
        import random
        return "".join(f"{random.randint(0, 9)}" for _ in range(10))
    
    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated."""
        if not self._authenticated:
            self.authenticate()
    
    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            HaasOnlineAPIError: If request fails
        """
        if not self.session:
            self._setup_session()
        
        # Prepare request parameters
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Add authentication parameters if authenticated
        if self._authenticated and params:
            params = params.copy()
            if self._user_id:
                params["userid"] = self._user_id
            if self._interface_key:
                params["interfacekey"] = self._interface_key
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                verify=self.config.connection.verify_ssl
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                raise HaasOnlineAPIError(f"Invalid JSON response: {response.text}")
            
            # Check for API-level errors
            if isinstance(response_data, dict) and not response_data.get("Success", True):
                error_msg = response_data.get("Error", "Unknown API error")
                raise HaasOnlineAPIError(error_msg, response.status_code, response_data)
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise HaasOnlineAPIError(f"Request failed: {e}")
    
    async def _make_async_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make asynchronous HTTP request with rate limiting."""
        if not self.async_session:
            await self._setup_async_session()
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Prepare request parameters
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Add authentication parameters if authenticated
        if self._authenticated and params:
            params = params.copy()
            if self._user_id:
                params["userid"] = self._user_id
            if self._interface_key:
                params["interfacekey"] = self._interface_key
        
        try:
            self.logger.debug(f"Making async {method} request to {url}")
            
            async with self.async_session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                ssl=self.config.connection.verify_ssl
            ) as response:
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    response_data = await response.json()
                except json.JSONDecodeError:
                    text = await response.text()
                    raise HaasOnlineAPIError(f"Invalid JSON response: {text}")
                
                # Check for API-level errors
                if isinstance(response_data, dict) and not response_data.get("Success", True):
                    error_msg = response_data.get("Error", "Unknown API error")
                    raise HaasOnlineAPIError(error_msg, response.status, response_data)
                
                return response_data
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Async request failed: {e}")
            raise HaasOnlineAPIError(f"Async request failed: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to HaasOnline server.
        
        Returns:
            True if connection successful
        """
        try:
            response = self._make_request(
                "GET",
                self.config.get_api_url("User"),
                params={"channel": "PING"}
            )
            return response.get("Success", False)
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information and capabilities.
        
        Returns:
            Server information dictionary
        """
        response = self._make_request(
            "GET",
            self.config.get_api_url("User"),
            params={"channel": "GET_SERVER_INFO"}
        )
        return response.get("Data", {})
    
    # Script Management Methods
    
    def get_script_record(self, request: ScriptRecordRequest) -> ScriptRecordResponse:
        """
        Get script record with full details.
        
        Args:
            request: Script record request
            
        Returns:
            Script record response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_script_record),
            params={
                "channel": "GET_SCRIPT_RECORD",
                "scriptid": request.script_id
            }
        )
        
        data = response.get("Data", {})
        return ScriptRecordResponse(
            script_id=data.get("ScriptId", request.script_id),
            name=data.get("Name", ""),
            content=data.get("Content", ""),
            script_type=data.get("ScriptType", 0),
            parameters=data.get("Parameters", {}),
            created_at=datetime.fromisoformat(data.get("CreatedAt", datetime.now().isoformat())),
            modified_at=datetime.fromisoformat(data.get("ModifiedAt", datetime.now().isoformat())),
            compile_logs=data.get("CompileLogs", []),
            is_valid=data.get("IsValid", False),
            error_message=data.get("ErrorMessage")
        )
    
    def execute_debug_test(self, request: DebugTestRequest) -> DebugTestResponse:
        """
        Execute debug test for script compilation.
        
        Args:
            request: Debug test request
            
        Returns:
            Debug test response
        """
        self._ensure_authenticated()
        
        params = {
            "channel": "EXECUTE_DEBUGTEST",
            "scriptid": request.script_id
        }
        
        if request.script_content:
            params["content"] = request.script_content
        if request.parameters:
            params["parameters"] = json.dumps(request.parameters)
        
        response = self._make_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.execute_debugtest),
            data=params
        )
        
        data = response.get("Data", {})
        return DebugTestResponse(
            success=response.get("Success", False),
            compilation_logs=data.get("CompilationLogs", []),
            errors=[
                CompilationError(
                    line_number=err.get("LineNumber", 0),
                    column=err.get("Column", 0),
                    error_type=err.get("Type", ""),
                    message=err.get("Message", ""),
                    suggestion=err.get("Suggestion")
                )
                for err in data.get("Errors", [])
            ],
            warnings=data.get("Warnings", []),
            execution_time_ms=data.get("ExecutionTimeMs", 0),
            memory_usage_mb=data.get("MemoryUsageMb", 0.0),
            is_valid=data.get("IsValid", False),
            error_message=data.get("ErrorMessage")
        )
    
    def execute_quick_test(self, request: QuickTestRequest) -> QuickTestResponse:
        """
        Execute quick test for script execution logic.
        
        Args:
            request: Quick test request
            
        Returns:
            Quick test response
        """
        self._ensure_authenticated()
        
        params = {
            "channel": "EXECUTE_QUICKTEST",
            "scriptid": request.script_id,
            "accountid": request.account_id,
            "market": request.market_tag,
            "interval": request.interval,
            "tradeamount": request.execution_amount,
            "leverage": request.leverage,
            "positionmode": request.position_mode
        }
        
        if request.script_content:
            params["content"] = request.script_content
        if request.parameters:
            params["parameters"] = json.dumps(request.parameters)
        
        response = self._make_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.execute_quicktest),
            data=params
        )
        
        data = response.get("Data", {})
        return QuickTestResponse(
            success=response.get("Success", False),
            execution_id=data.get("ExecutionId", ""),
            trades=[
                TradeResult(
                    timestamp=datetime.fromisoformat(trade.get("Timestamp")),
                    action=trade.get("Action", ""),
                    price=trade.get("Price", 0.0),
                    amount=trade.get("Amount", 0.0),
                    fee=trade.get("Fee", 0.0),
                    profit_loss=trade.get("ProfitLoss", 0.0),
                    balance_after=trade.get("BalanceAfter", 0.0)
                )
                for trade in data.get("Trades", [])
            ],
            final_balance=data.get("FinalBalance", 0.0),
            total_profit_loss=data.get("TotalProfitLoss", 0.0),
            execution_logs=data.get("ExecutionLogs", []),
            runtime_data=data.get("RuntimeData", {}),
            execution_time_ms=data.get("ExecutionTimeMs", 0),
            error_message=data.get("ErrorMessage")
        )    
  
  # Backtest Execution Methods
    
    def execute_backtest(self, request: BacktestRequest) -> BacktestResponse:
        """
        Execute backtest for script.
        
        Args:
            request: Backtest request
            
        Returns:
            Backtest response
        """
        self._ensure_authenticated()
        
        params = {
            "channel": "EXECUTE_BACKTEST",
            "scriptid": request.script_id,
            "accountid": request.account_id,
            "market": request.market_tag,
            "starttime": request.start_time,
            "endtime": request.end_time,
            "interval": request.interval,
            "tradeamount": request.execution_amount,
            "leverage": request.leverage,
            "positionmode": request.position_mode,
            "marginmode": request.margin_mode
        }
        
        if request.script_content:
            params["content"] = request.script_content
        if request.parameters:
            params["parameters"] = json.dumps(request.parameters)
        
        response = self._make_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.execute_backtest),
            data=params
        )
        
        data = response.get("Data", {})
        return BacktestResponse(
            success=response.get("Success", False),
            backtest_id=data.get("BacktestId", ""),
            execution_id=data.get("ExecutionId", ""),
            status=ExecutionStatus(data.get("Status", "queued")),
            estimated_completion_time=datetime.fromisoformat(data["EstimatedCompletion"]) if data.get("EstimatedCompletion") else None,
            error_message=data.get("ErrorMessage")
        )
    
    def get_execution_update(self, request: ExecutionUpdateRequest) -> ExecutionUpdateResponse:
        """
        Get execution update for running backtest.
        
        Args:
            request: Execution update request
            
        Returns:
            Execution update response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_execution_update),
            params={
                "channel": "GET_EXECUTION_UPDATE",
                "executionid": request.execution_id
            }
        )
        
        data = response.get("Data", {})
        progress_data = data.get("Progress", {})
        resource_data = data.get("ResourceUsage", {})
        
        return ExecutionUpdateResponse(
            execution_id=data.get("ExecutionId", request.execution_id),
            backtest_id=data.get("BacktestId", ""),
            status=ExecutionStatus(data.get("Status", "running")),
            progress=ExecutionProgress(
                percentage=progress_data.get("Percentage", 0.0),
                current_phase=progress_data.get("CurrentPhase", ""),
                processed_candles=progress_data.get("ProcessedCandles", 0),
                total_candles=progress_data.get("TotalCandles", 0),
                estimated_remaining_seconds=progress_data.get("EstimatedRemainingSeconds", 0),
                current_timestamp=datetime.fromisoformat(progress_data["CurrentTimestamp"]) if progress_data.get("CurrentTimestamp") else datetime.now()
            ),
            resource_usage=ResourceUsage(
                cpu_percentage=resource_data.get("CpuPercentage", 0.0),
                memory_mb=resource_data.get("MemoryMb", 0.0),
                disk_io_mb=resource_data.get("DiskIoMb", 0.0),
                network_io_mb=resource_data.get("NetworkIoMb", 0.0)
            ),
            started_at=datetime.fromisoformat(data["StartedAt"]) if data.get("StartedAt") else datetime.now(),
            last_update=datetime.fromisoformat(data["LastUpdate"]) if data.get("LastUpdate") else datetime.now(),
            error_message=data.get("ErrorMessage")
        )
    
    def get_execution_backtests(self, request: ExecutionBacktestsRequest) -> ExecutionBacktestsResponse:
        """
        Get list of running/completed backtests.
        
        Args:
            request: Execution backtests request
            
        Returns:
            Execution backtests response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.execution_backtests),
            params={
                "channel": "EXECUTION_BACKTESTS",
                "includecompleted": request.include_completed,
                "includefailed": request.include_failed
            }
        )
        
        data = response.get("Data", {})
        
        def parse_backtest_list(backtest_list: List[Dict]) -> List[RunningBacktest]:
            return [
                RunningBacktest(
                    backtest_id=bt.get("BacktestId", ""),
                    execution_id=bt.get("ExecutionId", ""),
                    script_name=bt.get("ScriptName", ""),
                    market_tag=bt.get("MarketTag", ""),
                    status=ExecutionStatus(bt.get("Status", "running")),
                    progress_percentage=bt.get("ProgressPercentage", 0.0),
                    started_at=datetime.fromisoformat(bt["StartedAt"]) if bt.get("StartedAt") else datetime.now(),
                    estimated_completion=datetime.fromisoformat(bt["EstimatedCompletion"]) if bt.get("EstimatedCompletion") else None
                )
                for bt in backtest_list
            ]
        
        return ExecutionBacktestsResponse(
            running_backtests=parse_backtest_list(data.get("RunningBacktests", [])),
            completed_backtests=parse_backtest_list(data.get("CompletedBacktests", [])),
            failed_backtests=parse_backtest_list(data.get("FailedBacktests", [])),
            total_count=data.get("TotalCount", 0)
        )
    
    # Results Retrieval Methods
    
    def get_backtest_runtime(self, request: BacktestRuntimeRequest) -> BacktestRuntimeResponse:
        """
        Get backtest runtime data and results.
        
        Args:
            request: Backtest runtime request
            
        Returns:
            Backtest runtime response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_backtest_runtime),
            params={
                "channel": "GET_BACKTEST_RUNTIME",
                "backtestid": request.backtest_id
            }
        )
        
        data = response.get("Data", {})
        metrics_data = data.get("Metrics", {})
        
        return BacktestRuntimeResponse(
            backtest_id=data.get("BacktestId", request.backtest_id),
            execution_id=data.get("ExecutionId", ""),
            status=ExecutionStatus(data.get("Status", "completed")),
            start_time=datetime.fromisoformat(data["StartTime"]) if data.get("StartTime") else datetime.now(),
            end_time=datetime.fromisoformat(data["EndTime"]) if data.get("EndTime") else None,
            duration_seconds=data.get("DurationSeconds", 0),
            trades=[
                TradeResult(
                    timestamp=datetime.fromisoformat(trade.get("Timestamp")),
                    action=trade.get("Action", ""),
                    price=trade.get("Price", 0.0),
                    amount=trade.get("Amount", 0.0),
                    fee=trade.get("Fee", 0.0),
                    profit_loss=trade.get("ProfitLoss", 0.0),
                    balance_after=trade.get("BalanceAfter", 0.0)
                )
                for trade in data.get("Trades", [])
            ],
            metrics=ExecutionMetrics(
                total_return=metrics_data.get("TotalReturn", 0.0),
                total_return_percentage=metrics_data.get("TotalReturnPercentage", 0.0),
                sharpe_ratio=metrics_data.get("SharpeRatio", 0.0),
                max_drawdown=metrics_data.get("MaxDrawdown", 0.0),
                max_drawdown_percentage=metrics_data.get("MaxDrawdownPercentage", 0.0),
                win_rate=metrics_data.get("WinRate", 0.0),
                profit_factor=metrics_data.get("ProfitFactor", 0.0),
                total_trades=metrics_data.get("TotalTrades", 0),
                winning_trades=metrics_data.get("WinningTrades", 0),
                losing_trades=metrics_data.get("LosingTrades", 0),
                avg_trade_duration_minutes=metrics_data.get("AvgTradeDurationMinutes", 0.0),
                avg_winning_trade=metrics_data.get("AvgWinningTrade", 0.0),
                avg_losing_trade=metrics_data.get("AvgLosingTrade", 0.0),
                largest_winning_trade=metrics_data.get("LargestWinningTrade", 0.0),
                largest_losing_trade=metrics_data.get("LargestLosingTrade", 0.0),
                volatility=metrics_data.get("Volatility", 0.0),
                calmar_ratio=metrics_data.get("CalmarRatio", 0.0),
                sortino_ratio=metrics_data.get("SortinoRatio", 0.0)
            ),
            final_balance=data.get("FinalBalance", 0.0),
            initial_balance=data.get("InitialBalance", 0.0),
            runtime_data=data.get("RuntimeData", {}),
            chart_data=data.get("ChartData")
        )
    
    def get_backtest_logs(self, request: BacktestLogsRequest) -> BacktestLogsResponse:
        """
        Get backtest execution logs.
        
        Args:
            request: Backtest logs request
            
        Returns:
            Backtest logs response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_backtest_logs),
            params={
                "channel": "GET_BACKTEST_LOGS",
                "backtestid": request.backtest_id,
                "startindex": request.start_index,
                "count": request.count
            }
        )
        
        data = response.get("Data", {})
        
        return BacktestLogsResponse(
            backtest_id=data.get("BacktestId", request.backtest_id),
            logs=[
                LogEntry(
                    timestamp=datetime.fromisoformat(log.get("Timestamp")),
                    level=LogLevel(log.get("Level", "info")),
                    message=log.get("Message", ""),
                    context=log.get("Context", {})
                )
                for log in data.get("Logs", [])
            ],
            total_count=data.get("TotalCount", 0),
            has_more=data.get("HasMore", False)
        )
    
    def get_backtest_chart(self, request: BacktestChartRequest) -> BacktestChartResponse:
        """
        Get backtest chart data partition.
        
        Args:
            request: Backtest chart request
            
        Returns:
            Backtest chart response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_backtest_chart_partition),
            params={
                "channel": "GET_BACKTEST_CHART_PARTITION",
                "backtestid": request.backtest_id,
                "partitionindex": request.partition_index
            }
        )
        
        data = response.get("Data", {})
        
        return BacktestChartResponse(
            backtest_id=data.get("BacktestId", request.backtest_id),
            partition_index=data.get("PartitionIndex", request.partition_index),
            data_points=[
                ChartDataPoint(
                    timestamp=datetime.fromisoformat(point.get("Timestamp")),
                    open_price=point.get("Open", 0.0),
                    high_price=point.get("High", 0.0),
                    low_price=point.get("Low", 0.0),
                    close_price=point.get("Close", 0.0),
                    volume=point.get("Volume", 0.0),
                    indicators=point.get("Indicators", {})
                )
                for point in data.get("DataPoints", [])
            ],
            total_partitions=data.get("TotalPartitions", 1),
            has_more=data.get("HasMore", False)
        )
    
    # History Management Methods
    
    def get_backtest_history(self, request: BacktestHistoryRequest) -> BacktestHistoryResponse:
        """
        Get backtest history within 48-hour window.
        
        Args:
            request: Backtest history request
            
        Returns:
            Backtest history response
        """
        self._ensure_authenticated()
        
        params = {
            "channel": "GET_BACKTEST_HISTORY",
            "limit": request.limit
        }
        
        if request.start_time:
            params["starttime"] = request.start_time
        if request.end_time:
            params["endtime"] = request.end_time
        
        response = self._make_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_backtest_history),
            params=params
        )
        
        data = response.get("Data", {})
        
        return BacktestHistoryResponse(
            backtests=[
                BacktestSummary(
                    backtest_id=bt.get("BacktestId", ""),
                    script_id=bt.get("ScriptId", ""),
                    script_name=bt.get("ScriptName", ""),
                    market_tag=bt.get("MarketTag", ""),
                    start_time=datetime.fromisoformat(bt["StartTime"]) if bt.get("StartTime") else datetime.now(),
                    end_time=datetime.fromisoformat(bt["EndTime"]) if bt.get("EndTime") else datetime.now(),
                    status=ExecutionStatus(bt.get("Status", "completed")),
                    total_return=bt.get("TotalReturn", 0.0),
                    max_drawdown=bt.get("MaxDrawdown", 0.0),
                    total_trades=bt.get("TotalTrades", 0),
                    created_at=datetime.fromisoformat(bt["CreatedAt"]) if bt.get("CreatedAt") else datetime.now(),
                    archived=bt.get("Archived", False)
                )
                for bt in data.get("Backtests", [])
            ],
            total_count=data.get("TotalCount", 0),
            has_more=data.get("HasMore", False)
        )
    
    def archive_backtest(self, request: ArchiveBacktestRequest) -> ArchiveBacktestResponse:
        """
        Archive backtest for permanent storage.
        
        Args:
            request: Archive backtest request
            
        Returns:
            Archive backtest response
        """
        self._ensure_authenticated()
        
        params = {
            "channel": "ARCHIVE_BACKTEST",
            "backtestid": request.backtest_id
        }
        
        if request.archive_name:
            params["archivename"] = request.archive_name
        
        response = self._make_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.archive_backtest),
            data=params
        )
        
        data = response.get("Data", {})
        
        return ArchiveBacktestResponse(
            success=response.get("Success", False),
            backtest_id=data.get("BacktestId", request.backtest_id),
            archive_id=data.get("ArchiveId", ""),
            archive_name=data.get("ArchiveName", ""),
            archived_at=datetime.fromisoformat(data["ArchivedAt"]) if data.get("ArchivedAt") else datetime.now(),
            error_message=data.get("ErrorMessage")
        )
    
    def delete_backtest(self, request: DeleteBacktestRequest) -> DeleteBacktestResponse:
        """
        Delete backtest to free resources.
        
        Args:
            request: Delete backtest request
            
        Returns:
            Delete backtest response
        """
        self._ensure_authenticated()
        
        response = self._make_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.delete_backtest),
            data={
                "channel": "DELETE_BACKTEST",
                "backtestid": request.backtest_id
            }
        )
        
        data = response.get("Data", {})
        
        return DeleteBacktestResponse(
            success=response.get("Success", False),
            backtest_id=data.get("BacktestId", request.backtest_id),
            deleted_at=datetime.fromisoformat(data["DeletedAt"]) if data.get("DeletedAt") else datetime.now(),
            error_message=data.get("ErrorMessage")
        )
    
    # Async versions of key methods
    
    async def execute_backtest_async(self, request: BacktestRequest) -> BacktestResponse:
        """Async version of execute_backtest."""
        self._ensure_authenticated()
        
        params = {
            "channel": "EXECUTE_BACKTEST",
            "scriptid": request.script_id,
            "accountid": request.account_id,
            "market": request.market_tag,
            "starttime": request.start_time,
            "endtime": request.end_time,
            "interval": request.interval,
            "tradeamount": request.execution_amount,
            "leverage": request.leverage,
            "positionmode": request.position_mode,
            "marginmode": request.margin_mode
        }
        
        if request.script_content:
            params["content"] = request.script_content
        if request.parameters:
            params["parameters"] = json.dumps(request.parameters)
        
        response = await self._make_async_request(
            "POST",
            self.config.get_api_url(self.config.endpoints.execute_backtest),
            data=params
        )
        
        data = response.get("Data", {})
        return BacktestResponse(
            success=response.get("Success", False),
            backtest_id=data.get("BacktestId", ""),
            execution_id=data.get("ExecutionId", ""),
            status=ExecutionStatus(data.get("Status", "queued")),
            estimated_completion_time=datetime.fromisoformat(data["EstimatedCompletion"]) if data.get("EstimatedCompletion") else None,
            error_message=data.get("ErrorMessage")
        )
    
    async def get_execution_update_async(self, request: ExecutionUpdateRequest) -> ExecutionUpdateResponse:
        """Async version of get_execution_update."""
        self._ensure_authenticated()
        
        response = await self._make_async_request(
            "GET",
            self.config.get_api_url(self.config.endpoints.get_execution_update),
            params={
                "channel": "GET_EXECUTION_UPDATE",
                "executionid": request.execution_id
            }
        )
        
        data = response.get("Data", {})
        progress_data = data.get("Progress", {})
        resource_data = data.get("ResourceUsage", {})
        
        return ExecutionUpdateResponse(
            execution_id=data.get("ExecutionId", request.execution_id),
            backtest_id=data.get("BacktestId", ""),
            status=ExecutionStatus(data.get("Status", "running")),
            progress=ExecutionProgress(
                percentage=progress_data.get("Percentage", 0.0),
                current_phase=progress_data.get("CurrentPhase", ""),
                processed_candles=progress_data.get("ProcessedCandles", 0),
                total_candles=progress_data.get("TotalCandles", 0),
                estimated_remaining_seconds=progress_data.get("EstimatedRemainingSeconds", 0),
                current_timestamp=datetime.fromisoformat(progress_data["CurrentTimestamp"]) if progress_data.get("CurrentTimestamp") else datetime.now()
            ),
            resource_usage=ResourceUsage(
                cpu_percentage=resource_data.get("CpuPercentage", 0.0),
                memory_mb=resource_data.get("MemoryMb", 0.0),
                disk_io_mb=resource_data.get("DiskIoMb", 0.0),
                network_io_mb=resource_data.get("NetworkIoMb", 0.0)
            ),
            started_at=datetime.fromisoformat(data["StartedAt"]) if data.get("StartedAt") else datetime.now(),
            last_update=datetime.fromisoformat(data["LastUpdate"]) if data.get("LastUpdate") else datetime.now(),
            error_message=data.get("ErrorMessage")
        )