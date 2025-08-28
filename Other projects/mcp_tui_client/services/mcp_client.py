"""
MCP Client Service

Enhanced service for communicating with the HaasOnline MCP server with comprehensive
connection management, retry logic, and error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union
import json
import aiohttp
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..utils.errors import (
    ConnectionError, APIError, ErrorCategory, ErrorSeverity, 
    ErrorContext, handle_error, error_handler
)
from ..utils.logging import get_logger, get_performance_logger, timer


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class MCPConfig:
    """MCP server configuration"""
    host: str = "localhost"
    port: int = 3002
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1000
    max_retry_delay: int = 30000
    use_ssl: bool = False
    api_key: Optional[str] = None
    username: Optional[str] = None
    auto_reconnect: bool = True
    connection_pool_size: int = 10
    keepalive_timeout: int = 30
    
    @property
    def base_url(self) -> str:
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


@dataclass
class ConnectionStats:
    """Connection statistics and metrics"""
    connected_at: Optional[datetime] = None
    last_request_at: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    reconnection_attempts: int = 0
    average_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    def add_response_time(self, response_time: float) -> None:
        """Add response time to statistics"""
        self.response_times.append(response_time)
        if len(self.response_times) > 100:  # Keep only last 100 measurements
            self.response_times.pop(0)
        self.average_response_time = sum(self.response_times) / len(self.response_times)


class ExponentialBackoff:
    """Exponential backoff strategy for retries"""
    
    def __init__(self, initial_delay: int = 1000, max_delay: int = 30000, multiplier: float = 2.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.current_delay = initial_delay
    
    def get_delay(self) -> float:
        """Get current delay in seconds"""
        delay = min(self.current_delay, self.max_delay)
        self.current_delay = int(self.current_delay * self.multiplier)
        return delay / 1000.0
    
    def reset(self) -> None:
        """Reset backoff to initial delay"""
        self.current_delay = self.initial_delay


class MCPClientService:
    """Enhanced service for MCP server communication"""
    
    def __init__(self, config: Union[MCPConfig, Dict[str, Any]]):
        if isinstance(config, dict):
            self.config = MCPConfig(**config)
        else:
            self.config = config
            
        self.session: Optional[aiohttp.ClientSession] = None
        self.state = ConnectionState.DISCONNECTED
        self.stats = ConnectionStats()
        self.backoff = ExponentialBackoff(
            self.config.retry_delay, 
            self.config.max_retry_delay
        )
        
        # Logging
        self.logger = get_logger(__name__, {"component": "mcp_client"})
        self.perf_logger = get_performance_logger(__name__)
        
        # Connection management
        self._connection_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._connection_callbacks: List[Callable[[ConnectionState], None]] = []
        
        # Request queue for connection recovery
        self._request_queue: List[Dict[str, Any]] = []
        self._max_queue_size = 100
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.state == ConnectionState.CONNECTED and self.session is not None
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "state": self.state.value,
            "base_url": self.config.base_url,
            "connected_at": self.stats.connected_at.isoformat() if self.stats.connected_at else None,
            "total_requests": self.stats.total_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": (
                (self.stats.total_requests - self.stats.failed_requests) / self.stats.total_requests * 100
                if self.stats.total_requests > 0 else 0
            ),
            "average_response_time": self.stats.average_response_time,
            "reconnection_attempts": self.stats.reconnection_attempts
        }
    
    def add_connection_callback(self, callback: Callable[[ConnectionState], None]) -> None:
        """Add connection state change callback"""
        self._connection_callbacks.append(callback)
    
    def remove_connection_callback(self, callback: Callable[[ConnectionState], None]) -> None:
        """Remove connection state change callback"""
        if callback in self._connection_callbacks:
            self._connection_callbacks.remove(callback)
    
    def _notify_connection_state_change(self, new_state: ConnectionState) -> None:
        """Notify all callbacks of connection state change"""
        old_state = self.state
        self.state = new_state
        
        self.logger.info(f"Connection state changed: {old_state.value} -> {new_state.value}")
        
        for callback in self._connection_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    @error_handler(category=ErrorCategory.CONNECTION, severity=ErrorSeverity.HIGH)
    async def connect(self) -> bool:
        """Establish MCP connection with retry logic and automatic reconnection"""
        async with self._connection_lock:
            if self.is_connected:
                return True
            
            self._notify_connection_state_change(ConnectionState.CONNECTING)
            
            try:
                # Create session with connection pooling
                connector = aiohttp.TCPConnector(
                    limit=self.config.connection_pool_size,
                    keepalive_timeout=self.config.keepalive_timeout,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                
                # Set up headers
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "MCP-TUI-Client/0.1.0"
                }
                
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers
                )
                
                # Test connection with health check
                await self._health_check()
                
                # Connection successful
                self.stats.connected_at = datetime.now()
                self.stats.reconnection_attempts = 0
                self.backoff.reset()
                
                self._notify_connection_state_change(ConnectionState.CONNECTED)
                
                # Start background tasks
                await self._start_background_tasks()
                
                self.logger.info(f"Successfully connected to MCP server at {self.config.base_url}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to connect to MCP server: {e}")
                self._notify_connection_state_change(ConnectionState.FAILED)
                
                if self.session:
                    await self.session.close()
                    self.session = None
                
                # Start auto-reconnection if enabled
                if self.config.auto_reconnect and not self._reconnect_task:
                    self._reconnect_task = asyncio.create_task(self._auto_reconnect())
                
                raise ConnectionError(f"Failed to connect to MCP server: {e}")
    
    async def disconnect(self) -> None:
        """Close MCP connection and cleanup resources"""
        async with self._connection_lock:
            self._notify_connection_state_change(ConnectionState.DISCONNECTED)
            
            # Cancel background tasks
            if self._reconnect_task:
                self._reconnect_task.cancel()
                self._reconnect_task = None
            
            if self._health_check_task:
                self._health_check_task.cancel()
                self._health_check_task = None
            
            # Close session
            if self.session:
                await self.session.close()
                self.session = None
            
            self.logger.info("Disconnected from MCP server")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks for connection monitoring"""
        # Start periodic health checks
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._periodic_health_check())
    
    async def _periodic_health_check(self) -> None:
        """Periodic health check to monitor connection"""
        while self.is_connected:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                if self.is_connected:
                    await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Health check failed: {e}")
                if self.config.auto_reconnect:
                    await self._trigger_reconnection()
                break
    
    async def _auto_reconnect(self) -> None:
        """Automatic reconnection with exponential backoff"""
        while self.state != ConnectionState.CONNECTED and self.config.auto_reconnect:
            try:
                self._notify_connection_state_change(ConnectionState.RECONNECTING)
                
                delay = self.backoff.get_delay()
                self.logger.info(f"Attempting reconnection in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
                
                self.stats.reconnection_attempts += 1
                
                if await self.connect():
                    self.logger.info("Reconnection successful")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Reconnection attempt failed: {e}")
                continue
        
        self._reconnect_task = None
    
    async def _trigger_reconnection(self) -> None:
        """Trigger reconnection process"""
        if self.config.auto_reconnect and not self._reconnect_task:
            self._notify_connection_state_change(ConnectionState.FAILED)
            self._reconnect_task = asyncio.create_task(self._auto_reconnect())
    
    async def _health_check(self) -> Dict[str, Any]:
        """Internal health check"""
        return await self._make_request("GET", "/health", skip_queue=True)
    
    async def health_check(self) -> Dict[str, Any]:
        """Public health check method"""
        return await self._health_check()
    
    @error_handler(category=ErrorCategory.API, severity=ErrorSeverity.MEDIUM)
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute MCP tool with comprehensive error handling and validation"""
        # Validate inputs
        if not tool_name:
            raise ValueError("Tool name cannot be empty")
        
        if not isinstance(parameters, dict):
            raise ValueError("Parameters must be a dictionary")
        
        # Create execution context
        context = ErrorContext(
            component="mcp_client",
            operation=f"call_tool:{tool_name}",
            additional_data={"tool_name": tool_name, "param_count": len(parameters)}
        )
        
        with timer(self.perf_logger, f"tool_execution:{tool_name}"):
            endpoint = f"/api/tools/{tool_name}"
            return await self._make_request("POST", endpoint, data=parameters)
    
    async def batch_operations(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple operations efficiently"""
        if not operations:
            return []
        
        self.logger.info(f"Executing batch of {len(operations)} operations")
        
        # Execute operations concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent operations
        
        async def execute_operation(operation: Dict[str, Any]) -> Any:
            async with semaphore:
                tool_name = operation.get("tool")
                params = operation.get("params", {})
                
                if not tool_name:
                    raise ValueError("Operation must specify 'tool' field")
                
                return await self.call_tool(tool_name, params)
        
        # Execute all operations
        tasks = [execute_operation(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch operation {i} failed: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "operation": operations[i]
                })
            else:
                processed_results.append({
                    "success": True,
                    "data": result,
                    "operation": operations[i]
                })
        
        return processed_results
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        skip_queue: bool = False
    ) -> Any:
        """Make HTTP request with comprehensive retry logic and error handling"""
        if not self.is_connected and not skip_queue:
            if self.config.auto_reconnect:
                # Queue request for later execution
                if len(self._request_queue) < self._max_queue_size:
                    self._request_queue.append({
                        "method": method,
                        "endpoint": endpoint,
                        "data": data,
                        "timestamp": time.time()
                    })
                    self.logger.info(f"Queued request {method} {endpoint} (queue size: {len(self._request_queue)})")
                
                # Trigger reconnection
                await self._trigger_reconnection()
                
                # Wait for connection or timeout
                timeout = 30  # 30 seconds timeout
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    await asyncio.sleep(0.1)
                
                if not self.is_connected:
                    raise ConnectionError("Failed to establish connection within timeout")
            else:
                raise ConnectionError("MCP client not connected")
        
        url = f"{self.config.base_url}{endpoint}"
        request_start = time.time()
        
        # Exponential backoff for this specific request
        request_backoff = ExponentialBackoff(
            self.config.retry_delay,
            self.config.max_retry_delay
        )
        
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.stats.total_requests += 1
                self.stats.last_request_at = datetime.now()
                
                # Prepare request
                kwargs = {"url": url}
                if data:
                    kwargs["json"] = data
                
                # Add authentication if available
                headers = {}
                if self.config.username and hasattr(self.session, '_default_headers'):
                    headers.update(self.session._default_headers)
                
                if headers:
                    kwargs["headers"] = headers
                
                # Make request
                async with self.session.request(method, **kwargs) as response:
                    # Record response time
                    response_time = time.time() - request_start
                    self.stats.add_response_time(response_time)
                    
                    # Handle HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise APIError(
                            f"HTTP {response.status}: {error_text}",
                            status_code=response.status
                        )
                    
                    # Parse response
                    try:
                        result = await response.json()
                    except json.JSONDecodeError:
                        # Handle non-JSON responses
                        text_result = await response.text()
                        return {"raw_response": text_result}
                    
                    # Handle API-level errors
                    if isinstance(result, dict):
                        if not result.get("success", True):
                            error_msg = result.get("error", "Unknown API error")
                            raise APIError(f"API Error: {error_msg}")
                        
                        # Return data field if present, otherwise full result
                        return result.get("data", result)
                    
                    return result
                    
            except (aiohttp.ClientError, asyncio.TimeoutError, APIError) as e:
                last_exception = e
                self.stats.failed_requests += 1
                
                if attempt == self.config.retry_attempts - 1:
                    self.logger.error(
                        f"Request failed after {self.config.retry_attempts} attempts: {e}",
                        method=method,
                        endpoint=endpoint,
                        attempt=attempt + 1
                    )
                    
                    # Trigger reconnection on connection errors
                    if isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError)):
                        await self._trigger_reconnection()
                    
                    raise APIError(f"Request failed: {e}") from e
                
                # Wait before retry with exponential backoff
                delay = request_backoff.get_delay()
                self.logger.warning(
                    f"Request attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}",
                    method=method,
                    endpoint=endpoint,
                    delay=delay
                )
                await asyncio.sleep(delay)
            
            except Exception as e:
                last_exception = e
                self.stats.failed_requests += 1
                self.logger.error(f"Unexpected error in request: {e}")
                raise APIError(f"Unexpected error: {e}") from e
        
        # This should never be reached, but just in case
        raise APIError(f"Request failed after all retries: {last_exception}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    # Bot Management Methods
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        """Get all trading bots"""
        return await self.call_tool("get_all_bots", {})
    
    async def get_bot_details(self, bot_id: str) -> Dict[str, Any]:
        """Get detailed bot information"""
        return await self.call_tool("get_bot_details", {"bot_id": bot_id})
    
    async def activate_bot(self, bot_id: str) -> None:
        """Activate a trading bot"""
        await self.call_tool("activate_bot", {"bot_id": bot_id})
    
    async def deactivate_bot(self, bot_id: str) -> None:
        """Deactivate a trading bot"""
        await self.call_tool("deactivate_bot", {"bot_id": bot_id})
    
    async def pause_bot(self, bot_id: str) -> None:
        """Pause a trading bot"""
        await self.call_tool("pause_bot", {"bot_id": bot_id})
    
    async def resume_bot(self, bot_id: str) -> None:
        """Resume a paused bot"""
        await self.call_tool("resume_bot", {"bot_id": bot_id})
    
    # Lab Management Methods
    async def get_all_labs(self) -> List[Dict[str, Any]]:
        """Get all backtesting labs"""
        return await self.call_tool("get_all_labs", {})
    
    async def get_lab_details(self, lab_id: str) -> Dict[str, Any]:
        """Get detailed lab information"""
        return await self.call_tool("get_lab_details", {"lab_id": lab_id})
    
    async def create_lab(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new backtesting lab"""
        return await self.call_tool("create_lab", config)
    
    async def clone_lab(self, lab_id: str, new_name: str) -> Dict[str, Any]:
        """Clone an existing lab"""
        return await self.call_tool("clone_lab", {
            "lab_id": lab_id,
            "new_name": new_name
        })
    
    async def execute_backtest_intelligent(
        self, 
        lab_id: str, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Execute intelligent backtest"""
        return await self.call_tool("execute_backtest_intelligent", {
            "lab_id": lab_id,
            "start_date": start_date,
            "end_date": end_date
        })
    
    # Script Management Methods
    async def get_all_scripts(self) -> List[Dict[str, Any]]:
        """Get all available scripts"""
        return await self.call_tool("get_all_scripts", {})
    
    async def get_script_details(self, script_id: str) -> Dict[str, Any]:
        """Get detailed script information"""
        return await self.call_tool("get_script_details", {"script_id": script_id})
    
    async def add_script(
        self, 
        script_name: str, 
        script_content: str, 
        description: str = ""
    ) -> Dict[str, Any]:
        """Add a new script"""
        return await self.call_tool("add_script", {
            "script_name": script_name,
            "script_content": script_content,
            "description": description
        })
    
    async def save_script(
        self, 
        script_id: str, 
        source_code: str, 
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save script with validation"""
        return await self.call_tool("save_script", {
            "script_id": script_id,
            "source_code": source_code,
            "settings": settings or {}
        })
    
    # Market Data Methods
    async def get_all_markets(self) -> List[Dict[str, Any]]:
        """Get all available markets"""
        return await self.call_tool("get_all_markets", {})
    
    async def get_market_snapshot(self, market_tag: str) -> Dict[str, Any]:
        """Get market snapshot data"""
        return await self.call_tool("get_market_snapshot", {
            "market_tag": market_tag
        })
    
    # Account Management Methods
    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all user accounts"""
        return await self.call_tool("get_all_accounts", {})
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get account balance"""
        return await self.call_tool("get_account_balance", {
            "account_id": account_id
        })
    
    # System Status Methods
    async def get_haas_status(self) -> Dict[str, Any]:
        """Get HaasOnline system status"""
        return await self.call_tool("get_haas_status", {})  
  
    # ==================== Bot Management Methods ====================
    
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        """Get all trading bots"""
        return await self.call_tool("get_all_bots", {})
    
    async def get_bot_details(self, bot_id: str) -> Dict[str, Any]:
        """Get detailed bot information"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("get_bot_details", {"bot_id": bot_id})
    
    async def activate_bot(self, bot_id: str) -> Dict[str, Any]:
        """Activate a trading bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("activate_bot", {"bot_id": bot_id})
    
    async def deactivate_bot(self, bot_id: str) -> Dict[str, Any]:
        """Deactivate a trading bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("deactivate_bot", {"bot_id": bot_id})
    
    async def pause_bot(self, bot_id: str) -> Dict[str, Any]:
        """Pause a trading bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("pause_bot", {"bot_id": bot_id})
    
    async def resume_bot(self, bot_id: str) -> Dict[str, Any]:
        """Resume a paused bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("resume_bot", {"bot_id": bot_id})
    
    async def delete_bot(self, bot_id: str) -> Dict[str, Any]:
        """Delete a trading bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        return await self.call_tool("delete_bot", {"bot_id": bot_id})
    
    async def create_bot_from_lab(
        self, 
        lab_id: str, 
        bot_name: str, 
        account_id: str
    ) -> Dict[str, Any]:
        """Create a bot from lab results"""
        if not all([lab_id, bot_name, account_id]):
            raise ValueError("Lab ID, bot name, and account ID are required")
        
        return await self.call_tool("create_bot_from_lab", {
            "lab_id": lab_id,
            "bot_name": bot_name,
            "account_id": account_id
        })
    
    async def get_bot_trades(self, bot_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get trade history for a bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        
        return await self.call_tool("get_bot_trades", {
            "bot_id": bot_id,
            "limit": limit
        })
    
    async def get_bot_positions(self, bot_id: str) -> Dict[str, Any]:
        """Get current positions for a bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        
        return await self.call_tool("get_bot_positions", {
            "bot_id": bot_id
        })
    
    async def get_bot_performance_history(self, bot_id: str, timeframe: str = "24h") -> Dict[str, Any]:
        """Get performance history for a bot"""
        if not bot_id:
            raise ValueError("Bot ID cannot be empty")
        
        return await self.call_tool("get_bot_performance_history", {
            "bot_id": bot_id,
            "timeframe": timeframe
        })
    
    # ==================== Lab Management Methods ====================
    
    async def get_all_labs(self) -> List[Dict[str, Any]]:
        """Get all backtesting labs"""
        return await self.call_tool("get_all_labs", {})
    
    async def get_lab_details(self, lab_id: str) -> Dict[str, Any]:
        """Get detailed lab information"""
        if not lab_id:
            raise ValueError("Lab ID cannot be empty")
        return await self.call_tool("get_lab_details", {"lab_id": lab_id})
    
    async def create_lab(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new backtesting lab"""
        required_fields = ["lab_name", "script_id", "trading_pair"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return await self.call_tool("create_lab", config)
    
    async def clone_lab(self, lab_id: str, new_name: str) -> Dict[str, Any]:
        """Clone an existing lab"""
        if not all([lab_id, new_name]):
            raise ValueError("Lab ID and new name are required")
        
        return await self.call_tool("clone_lab", {
            "lab_id": lab_id,
            "new_name": new_name
        })
    
    async def bulk_clone_labs(
        self, 
        lab_id: str, 
        markets: List[str], 
        name_template: str = "{original_name}_{market}"
    ) -> List[Dict[str, Any]]:
        """Clone a lab across multiple markets"""
        if not all([lab_id, markets]):
            raise ValueError("Lab ID and markets list are required")
        
        return await self.call_tool("bulk_clone_labs", {
            "lab_id": lab_id,
            "markets": markets,
            "name_template": name_template
        })
    
    async def execute_backtest_intelligent(
        self, 
        lab_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        auto_adjust: bool = True
    ) -> Dict[str, Any]:
        """Execute intelligent backtest with automatic period adjustment"""
        if not lab_id:
            raise ValueError("Lab ID cannot be empty")
        
        params = {
            "lab_id": lab_id,
            "auto_adjust": auto_adjust
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self.call_tool("execute_backtest_intelligent", params)
    
    async def get_backtest_results(self, lab_id: str) -> Dict[str, Any]:
        """Get backtest results for a lab"""
        if not lab_id:
            raise ValueError("Lab ID cannot be empty")
        return await self.call_tool("get_backtest_results", {"lab_id": lab_id})
    
    async def optimize_parameters(
        self, 
        lab_id: str, 
        optimization_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run parameter optimization on a lab"""
        if not all([lab_id, optimization_config]):
            raise ValueError("Lab ID and optimization config are required")
        
        return await self.call_tool("optimize_parameters", {
            "lab_id": lab_id,
            "config": optimization_config
        })
    
    async def delete_lab(self, lab_id: str) -> Dict[str, Any]:
        """Delete a backtesting lab"""
        if not lab_id:
            raise ValueError("Lab ID cannot be empty")
        return await self.call_tool("delete_lab", {"lab_id": lab_id})
    
    # ==================== Script Management Methods ====================
    
    async def get_all_scripts(self) -> List[Dict[str, Any]]:
        """Get all available scripts"""
        return await self.call_tool("get_all_scripts", {})
    
    async def get_script_details(self, script_id: str) -> Dict[str, Any]:
        """Get detailed script information"""
        if not script_id:
            raise ValueError("Script ID cannot be empty")
        return await self.call_tool("get_script_details", {"script_id": script_id})
    
    async def add_script(
        self, 
        script_name: str, 
        script_content: str, 
        description: str = "",
        folder: str = ""
    ) -> Dict[str, Any]:
        """Add a new script"""
        if not all([script_name, script_content]):
            raise ValueError("Script name and content are required")
        
        return await self.call_tool("add_script", {
            "script_name": script_name,
            "script_content": script_content,
            "description": description,
            "folder": folder
        })
    
    async def save_script(
        self, 
        script_id: str, 
        source_code: str, 
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save script with validation"""
        if not all([script_id, source_code]):
            raise ValueError("Script ID and source code are required")
        
        return await self.call_tool("save_script", {
            "script_id": script_id,
            "source_code": source_code,
            "settings": settings or {}
        })
    
    async def compile_script(self, script_id: str) -> Dict[str, Any]:
        """Compile a script and return compilation results"""
        if not script_id:
            raise ValueError("Script ID cannot be empty")
        return await self.call_tool("compile_script", {"script_id": script_id})
    
    async def validate_script(
        self, 
        script_content: str, 
        quick_validation: bool = True
    ) -> Dict[str, Any]:
        """Validate script syntax and structure"""
        if not script_content:
            raise ValueError("Script content cannot be empty")
        
        return await self.call_tool("validate_script", {
            "script_content": script_content,
            "quick_validation": quick_validation
        })
    
    async def delete_script(self, script_id: str) -> Dict[str, Any]:
        """Delete a script"""
        if not script_id:
            raise ValueError("Script ID cannot be empty")
        return await self.call_tool("delete_script", {"script_id": script_id})
    
    # ==================== Market Data Methods ====================
    
    async def get_all_markets(self) -> List[Dict[str, Any]]:
        """Get all available markets"""
        return await self.call_tool("get_all_markets", {})
    
    async def get_market_snapshot(self, market_tag: str) -> Dict[str, Any]:
        """Get market snapshot data"""
        if not market_tag:
            raise ValueError("Market tag cannot be empty")
        return await self.call_tool("get_market_snapshot", {"market_tag": market_tag})
    
    async def get_market_history(
        self, 
        market_tag: str, 
        interval: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Get historical market data"""
        if not market_tag:
            raise ValueError("Market tag cannot be empty")
        
        params = {
            "market_tag": market_tag,
            "interval": interval,
            "limit": limit
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self.call_tool("get_market_history", params)
    
    async def get_orderbook(self, market_tag: str, depth: int = 20) -> Dict[str, Any]:
        """Get market order book"""
        if not market_tag:
            raise ValueError("Market tag cannot be empty")
        
        return await self.call_tool("get_orderbook", {
            "market_tag": market_tag,
            "depth": depth
        })
    
    async def get_trade_history(
        self, 
        market_tag: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get recent trade history for a market"""
        if not market_tag:
            raise ValueError("Market tag cannot be empty")
        
        return await self.call_tool("get_trade_history", {
            "market_tag": market_tag,
            "limit": limit
        })
    
    # ==================== Account Management Methods ====================
    
    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all user accounts"""
        return await self.call_tool("get_all_accounts", {})
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get account balance"""
        if not account_id:
            raise ValueError("Account ID cannot be empty")
        return await self.call_tool("get_account_balance", {"account_id": account_id})
    
    async def get_account_positions(self, account_id: str) -> Dict[str, Any]:
        """Get account positions"""
        if not account_id:
            raise ValueError("Account ID cannot be empty")
        return await self.call_tool("get_account_positions", {"account_id": account_id})
    
    async def get_account_orders(
        self, 
        account_id: str, 
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get account orders"""
        if not account_id:
            raise ValueError("Account ID cannot be empty")
        
        params = {"account_id": account_id}
        if status:
            params["status"] = status
        
        return await self.call_tool("get_account_orders", params)
    
    async def get_account_trade_history(
        self, 
        account_id: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get account trade history"""
        if not account_id:
            raise ValueError("Account ID cannot be empty")
        
        return await self.call_tool("get_account_trade_history", {
            "account_id": account_id,
            "limit": limit
        })
    
    # ==================== System Status Methods ====================
    
    async def get_haas_status(self) -> Dict[str, Any]:
        """Get HaasOnline system status"""
        return await self.call_tool("get_haas_status", {})
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return await self.call_tool("get_system_info", {})
    
    async def get_api_limits(self) -> Dict[str, Any]:
        """Get API rate limits and usage"""
        return await self.call_tool("get_api_limits", {})
    
    # ==================== Utility Methods ====================
    
    async def ping(self) -> Dict[str, Any]:
        """Simple ping to test connectivity"""
        start_time = time.time()
        result = await self._make_request("GET", "/ping")
        response_time = time.time() - start_time
        
        return {
            "success": True,
            "response_time_ms": response_time * 1000,
            "server_time": result.get("timestamp"),
            "message": result.get("message", "pong")
        }
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get server timestamp"""
        return await self.call_tool("get_server_time", {})
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        result = await self._make_request("GET", "/api/tools")
        return result.get("tools", [])
    
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get schema for a specific tool"""
        if not tool_name:
            raise ValueError("Tool name cannot be empty")
        
        return await self._make_request("GET", f"/api/tools/{tool_name}/schema")
    
    # ==================== Advanced Operations ====================
    
    async def execute_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow definition"""
        if not workflow_definition:
            raise ValueError("Workflow definition cannot be empty")
        
        return await self.call_tool("execute_workflow", {
            "workflow": workflow_definition
        })
    
    async def get_performance_metrics(
        self, 
        resource_type: str, 
        resource_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for a resource"""
        if not all([resource_type, resource_id]):
            raise ValueError("Resource type and ID are required")
        
        params = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self.call_tool("get_performance_metrics", params)
    
    async def export_data(
        self, 
        data_type: str, 
        resource_id: str,
        format: str = "json",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Export data in various formats"""
        if not all([data_type, resource_id]):
            raise ValueError("Data type and resource ID are required")
        
        return await self.call_tool("export_data", {
            "data_type": data_type,
            "resource_id": resource_id,
            "format": format,
            "options": options or {}
        })