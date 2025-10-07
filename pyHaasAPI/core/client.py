"""
Async HTTP client for pyHaasAPI v2

Provides async HTTP client with aiohttp, connection pooling, request/response middleware,
retry logic with exponential backoff, rate limiting, and comprehensive logging.
"""

import asyncio
import time
from typing import Any, Dict, Optional, Union, List, Callable, Awaitable
from urllib.parse import urljoin, urlparse
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError, ClientResponse
from aiohttp.connector import TCPConnector
from aiohttp.helpers import BasicAuth
from pydantic import ValidationError

from ..config.api_config import APIConfig
from ..exceptions import (
    NetworkError, ConnectionError, TimeoutError, APIError, 
    APIRateLimitError, APITimeoutError, APIServerError, APIClientError, APIResponseError
)
from .logging import get_logger, RequestLogger, PerformanceLogger


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire rate limit permission"""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
            
            # Check if we can make a request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recursively try again after waiting
                    await self.acquire()
                    return
            
            # Record this request
            self.requests.append(now)


class RetryHandler:
    """Retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int, base_delay: float, backoff_factor: float):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(
        self, 
        operation: Callable[[], Awaitable[Any]], 
        operation_name: str = "operation"
    ) -> Any:
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation()
            except (ConnectionError, TimeoutError, APIServerError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (self.backoff_factor ** attempt)
                
                logger = get_logger("retry")
                logger.warning(
                    f"Retry {attempt + 1}/{self.max_retries} for {operation_name} after {delay:.2f}s",
                    extra={"attempt": attempt + 1, "max_retries": self.max_retries, "delay": delay}
                )
                
                await asyncio.sleep(delay)
            except (APIClientError, ValidationError) as e:
                # Don't retry client errors
                raise e
        
        # If we get here, all retries failed
        raise last_exception


class AsyncHaasClient:
    """
    Async HTTP client for HaasOnline API
    
    Provides comprehensive HTTP client functionality with connection pooling,
    rate limiting, retry logic, and comprehensive logging.
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests, 
            config.rate_limit_window
        )
        self.retry_handler = RetryHandler(
            config.max_retries,
            config.retry_delay,
            config.retry_backoff_factor
        )
        
        # Logging
        self.logger = get_logger("client")
        self.request_logger = RequestLogger(config.logging)
        self.performance_logger = PerformanceLogger(config.logging)
        
        # Connection state
        self._connected = False
        self._connection_lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self) -> None:
        """Establish connection to the API"""
        async with self._connection_lock:
            if self._connected:
                return
            
            try:
                # Create connector with connection pooling
                connector = TCPConnector(
                    limit=self.config.max_connections,
                    limit_per_host=self.config.max_keepalive_connections,
                    keepalive_timeout=self.config.keepalive_timeout,
                    enable_cleanup_closed=True,
                    ssl=self.config.verify_ssl
                )
                
                # Create timeout configuration
                timeout = ClientTimeout(
                    total=self.config.timeout,
                    connect=10.0,
                    sock_read=30.0
                )
                
                # Create session
                self.session = ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        "User-Agent": "pyHaasAPI-v2/2.0.0",
                        "Accept": "application/json, text/javascript, */*; q=0.1",
                        "Content-Type": "application/json"
                    }
                )
                
                self._connected = True
                self.logger.info(f"Connected to {self.config.full_url}")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to {self.config.full_url}: {e}")
                raise ConnectionError(f"Failed to connect: {e}")
    
    async def close(self) -> None:
        """Close the connection"""
        async with self._connection_lock:
            if self.session and not self.session.closed:
                await self.session.close()
            self._connected = False
            self.logger.info("Connection closed")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> ClientResponse:
        """Make HTTP request with comprehensive error handling"""
        
        if not self._connected:
            await self.connect()
        
        # Build URL
        # Ensure base_url respects trailing slash semantics
        base = self.config.full_url
        url = urljoin(base if base.endswith('/') else base + '/', endpoint.lstrip('/'))
        
        # Prepare headers
        request_headers = dict(headers) if headers else {}
        # Encourage server to return JSON rather than HTML
        request_headers.setdefault("Accept", "application/json, text/javascript, */*; q=0.1")
        # Indicate AJAX-style request for some servers that gate JSON behind XHR
        request_headers.setdefault("X-Requested-With", "XMLHttpRequest")
        if self.config.is_authenticated:
            request_headers.update(self.config.get_auth_headers())
        
        # Prepare request data
        request_data = None
        if data is not None:
            if isinstance(data, dict):
                # Many Haas endpoints expect x-www-form-urlencoded, not multipart
                from urllib.parse import urlencode
                request_data = urlencode(data)
                request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            else:
                request_data = data
        
        # Log request
        self.request_logger.log_request(
            method=method,
            url=url,
            headers=request_headers,
            body=data
        )
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Make request with retry logic
        async def _request():
            start_time = time.time()
            
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=request_data,
                    headers=request_headers,
                    timeout=timeout or self.config.timeout
                ) as response:
                    
                    # Read response body
                    response_data = await response.text()
                    duration = time.time() - start_time
                    
                    # Log response
                    self.request_logger.log_response(
                        method=method,
                        url=url,
                        status_code=response.status,
                        headers=dict(response.headers),
                        body=response_data,
                        duration=duration
                    )
                    
                    # Handle response errors
                    await self._handle_response_error(response, response_data)
                    
                    return response
                    
            except asyncio.TimeoutError:
                raise APITimeoutError(message=f"Request to {url} timed out")
            except ClientConnectorError as e:
                raise ConnectionError(message=f"Connection error to {url}: {e}")
            except Exception as e:
                raise APIError(message=f"Request to {url} failed: {e}")
        
        return await self.retry_handler.execute_with_retry(_request, f"{method} {endpoint}")
    
    async def _handle_response_error(self, response: ClientResponse, response_data: str) -> None:
        """Handle HTTP response errors"""
        if response.status < 400:
            return
        
        # Try to parse error response
        error_message = f"HTTP {response.status}"
        try:
            import json
            error_data = json.loads(response_data)
            if isinstance(error_data, dict) and "Error" in error_data:
                error_message = error_data["Error"]
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Raise appropriate exception based on status code
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise APIRateLimitError(error_message, retry_after=retry_after_int)
        elif 400 <= response.status < 500:
            raise APIClientError(error_message)
        elif 500 <= response.status < 600:
            raise APIServerError(error_message)
        else:
            raise APIError(error_message)
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> ClientResponse:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params, headers=headers, timeout=timeout)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> ClientResponse:
        """Make POST request"""
        return await self._make_request("POST", endpoint, params=params, data=data, headers=headers, timeout=timeout)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> ClientResponse:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, params=params, data=data, headers=headers, timeout=timeout)
    
    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> ClientResponse:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, params=params, headers=headers, timeout=timeout)
    
    async def request_json(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make request and return JSON response"""
        response = await self._make_request(method, endpoint, params, data, headers, timeout)

        try:
            # Parse JSON regardless of Content-Type; fail with clear context
            return await response.json(content_type=None)
        except Exception as e:
            body_preview = (await response.text())[:300]
            raise APIResponseError(
                f"Failed to parse JSON (ct={response.headers.get('Content-Type')}, status={response.status}). "
                f"Body preview: {body_preview}"
            )
    
    async def get_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make GET request and return JSON response"""
        return await self.request_json("GET", endpoint, params=params, headers=headers, timeout=timeout)
    
    async def post_json(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make POST request and return JSON response"""
        return await self.request_json("POST", endpoint, params=params, data=data, headers=headers, timeout=timeout)
    
    async def execute(
        self,
        endpoint: str,
        method: str = "POST",
        query_params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute API request using the endpoint exactly as provided.
        
        The caller must pass the full PHP endpoint path (e.g., "/LabsAPI.php").
        Query parameters are forwarded via the request's params.
        
        Args:
            endpoint: Full endpoint path including .php (e.g., "/BacktestAPI.php")
            method: HTTP method (GET, POST, etc.)
            query_params: Query parameters including channel
            data: Request data for POST requests
            headers: Additional headers
            timeout: Request timeout
            
        Returns:
            Dictionary response from the API
        """
        full_endpoint = endpoint
        if method.upper() == "GET":
            return await self.get_json(full_endpoint, params=query_params, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            return await self.post_json(full_endpoint, data=data, params=query_params, headers=headers, timeout=timeout)
        else:
            return await self.request_json(method, full_endpoint, params=query_params, data=data, headers=headers, timeout=timeout)
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self.session is not None and not self.session.closed
    
    async def health_check(self) -> bool:
        """Perform health check on the API"""
        try:
            response = await self.get("/UserAPI.php?channel=REFRESH_LICENSE", timeout=5.0)
            return response.status == 200
        except Exception:
            return False


# Synchronous wrapper for backward compatibility
class HaasClient:
    """
    Synchronous wrapper for AsyncHaasClient
    
    Provides synchronous interface for backward compatibility.
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self._async_client: Optional[AsyncHaasClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def __enter__(self):
        """Context manager entry"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._async_client = self._loop.run_until_complete(AsyncHaasClient(self.config).__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._async_client and self._loop:
            self._loop.run_until_complete(self._async_client.__aexit__(exc_type, exc_val, exc_tb))
            self._loop.close()
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        if not self._loop:
            raise RuntimeError("Client not initialized. Use context manager.")
        return self._loop.run_until_complete(coro)
    
    def get(self, endpoint: str, **kwargs) -> ClientResponse:
        """Sync GET request"""
        return self._run_async(self._async_client.get(endpoint, **kwargs))
    
    def post(self, endpoint: str, **kwargs) -> ClientResponse:
        """Sync POST request"""
        return self._run_async(self._async_client.post(endpoint, **kwargs))
    
    def put(self, endpoint: str, **kwargs) -> ClientResponse:
        """Sync PUT request"""
        return self._run_async(self._async_client.put(endpoint, **kwargs))
    
    def delete(self, endpoint: str, **kwargs) -> ClientResponse:
        """Sync DELETE request"""
        return self._run_async(self._async_client.delete(endpoint, **kwargs))
    
    def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Sync GET JSON request"""
        return self._run_async(self._async_client.get_json(endpoint, **kwargs))
    
    def post_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Sync POST JSON request"""
        return self._run_async(self._async_client.post_json(endpoint, **kwargs))
    
    def health_check(self) -> bool:
        """Sync health check"""
        return self._run_async(self._async_client.health_check())
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._async_client and self._async_client.is_connected
