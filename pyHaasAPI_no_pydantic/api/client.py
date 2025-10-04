"""
HTTP client wrapper for pyHaasAPI_no_pydantic

Provides a simple HTTP client interface for API operations
without external dependencies like aiohttp or requests.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


logger = logging.getLogger(__name__)


class APIClient:
    """
    Simple HTTP client for API operations
    
    Provides basic HTTP functionality without external dependencies,
    using only Python standard library.
    """
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8090",
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = headers or {
            'Content-Type': 'application/json',
            'User-Agent': 'pyHaasAPI_no_pydantic/1.0.0'
        }
        self.logger = logger
    
    def _make_url(self, endpoint: str) -> str:
        """Make full URL from endpoint"""
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        return urljoin(self.base_url + '/', endpoint)
    
    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        # Add query parameters
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"
        
        # Prepare headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Prepare request
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
            request_headers['Content-Length'] = str(len(request_data))
        
        # Create request
        request = Request(url, data=request_data, headers=request_headers, method=method)
        
        try:
            # Make request
            with urlopen(request, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                status_code = response.getcode()
                
                # Parse JSON response
                try:
                    result = json.loads(response_data)
                except json.JSONDecodeError:
                    result = {"Success": False, "Error": "Invalid JSON response", "Data": response_data}
                
                # Check for API errors
                if not result.get("Success", False):
                    error_msg = result.get("Error", "Unknown API error")
                    raise APIResponseError(url, status_code, result, {"error": error_msg})
                
                return result
                
        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            raise APIConnectionError(url, error_msg, {"status_code": e.code, "reason": e.reason})
        except URLError as e:
            error_msg = f"URL error: {e.reason}"
            raise APIConnectionError(url, error_msg, {"reason": e.reason})
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            raise APIConnectionError(url, error_msg, {"original_error": str(e)})
    
    async def get_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make GET request and return JSON response"""
        url = self._make_url(endpoint)
        self.logger.debug(f"GET {url} with params: {params}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            'GET',
            url,
            None,
            params,
            headers
        )
    
    async def post_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make POST request and return JSON response"""
        url = self._make_url(endpoint)
        self.logger.debug(f"POST {url} with data: {data}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            'POST',
            url,
            data,
            None,
            headers
        )
    
    async def put_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make PUT request and return JSON response"""
        url = self._make_url(endpoint)
        self.logger.debug(f"PUT {url} with data: {data}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            'PUT',
            url,
            data,
            None,
            headers
        )
    
    async def delete_json(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request and return JSON response"""
        url = self._make_url(endpoint)
        self.logger.debug(f"DELETE {url}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            'DELETE',
            url,
            None,
            None,
            headers
        )
    
    async def execute_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute HTTP request with specified method"""
        url = self._make_url(endpoint)
        self.logger.debug(f"{method} {url}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            method,
            url,
            data,
            params,
            headers
        )


# Import here to avoid circular imports
from .exceptions import APIConnectionError, APIResponseError



