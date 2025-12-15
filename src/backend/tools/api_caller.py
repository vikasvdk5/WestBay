"""
API calling tool for making HTTP requests to external APIs.
Handles authentication, retries, and response parsing.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import json

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class APICallerTool:
    """
    Tool for making HTTP API calls to external services.
    Supports authentication, retries, and structured response handling.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize API caller tool.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            default_headers: Default headers for all requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        
        logger.info("API Caller Tool initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def call_api(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.GET,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        auth: Optional[tuple] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key"
    ) -> Dict[str, Any]:
        """
        Make an API call.
        
        Args:
            url: API endpoint URL
            method: HTTP method
            headers: Additional headers
            params: Query parameters
            data: Form data
            json_body: JSON request body
            auth: Basic auth tuple (username, password)
            api_key: API key for authentication
            api_key_header: Header name for API key
            
        Returns:
            Dictionary with response data and metadata
        """
        start_time = time.time()
        
        # Prepare headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Add API key if provided
        if api_key:
            request_headers[api_key_header] = api_key
        
        try:
            logger.info(f"Calling API: {method.value} {url}")
            
            # Make request
            response = self.session.request(
                method=method.value,
                url=url,
                headers=request_headers,
                params=params,
                data=data,
                json=json_body,
                auth=auth,
                timeout=self.timeout
            )
            
            # Calculate request time
            request_time = time.time() - start_time
            
            # Handle response
            if response.status_code >= 200 and response.status_code < 300:
                return self._success_result(response, request_time)
            else:
                return self._error_result(
                    url,
                    f"HTTP {response.status_code}",
                    response.text,
                    response.status_code
                )
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling API: {url}")
            return self._error_result(url, "Timeout", f"Request exceeded {self.timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error calling API: {url}: {e}")
            return self._error_result(url, "Connection Error", str(e))
        
        except Exception as e:
            logger.error(f"Error calling API {url}: {e}")
            return self._error_result(url, "Error", str(e))
    
    def call_rest_api(
        self,
        base_url: str,
        endpoint: str,
        method: HTTPMethod = HTTPMethod.GET,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convenience method for calling REST APIs.
        
        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            method: HTTP method
            **kwargs: Additional arguments passed to call_api
            
        Returns:
            API response dictionary
        """
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        return self.call_api(url, method, **kwargs)
    
    def _success_result(
        self,
        response: requests.Response,
        request_time: float
    ) -> Dict[str, Any]:
        """
        Create success result dictionary.
        
        Args:
            response: HTTP response object
            request_time: Time taken for request
            
        Returns:
            Success result dictionary
        """
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        return {
            "status": "success",
            "status_code": response.status_code,
            "data": response_data,
            "headers": dict(response.headers),
            "url": response.url,
            "request_time": round(request_time, 2),
            "retrieved_at": datetime.now().isoformat()
        }
    
    def _error_result(
        self,
        url: str,
        error_type: str,
        error_message: str,
        status_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create error result dictionary.
        
        Args:
            url: URL that failed
            error_type: Type of error
            error_message: Error message
            status_code: HTTP status code if applicable
            
        Returns:
            Error result dictionary
        """
        return {
            "status": "error",
            "status_code": status_code,
            "error_type": error_type,
            "error_message": error_message,
            "url": url,
            "retrieved_at": datetime.now().isoformat()
        }
    
    def batch_api_calls(
        self,
        requests: List[Dict[str, Any]],
        delay_between_calls: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Make multiple API calls with delay between them.
        
        Args:
            requests: List of request specifications (each a dict with call_api args)
            delay_between_calls: Delay in seconds between calls
            
        Returns:
            List of API response dictionaries
        """
        results = []
        
        logger.info(f"Making {len(requests)} API calls")
        
        for i, req_spec in enumerate(requests):
            result = self.call_api(**req_spec)
            results.append(result)
            
            # Add delay between requests (except for last one)
            if i < len(requests) - 1:
                time.sleep(delay_between_calls)
        
        successful = len([r for r in results if r["status"] == "success"])
        logger.info(f"Completed {successful}/{len(requests)} API calls successfully")
        
        return results


# Predefined API configurations
API_CONFIGS = {
    "market_data": {
        "base_url": "https://api.marketdata.example.com/v1",
        "auth_type": "api_key",
        "rate_limit": 100  # requests per minute
    },
    "financial_data": {
        "base_url": "https://api.financial.example.com/v2",
        "auth_type": "bearer",
        "rate_limit": 60
    }
}


def create_api_caller(
    timeout: int = 30,
    max_retries: int = 3
) -> APICallerTool:
    """
    Factory function to create an API caller tool.
    
    Args:
        timeout: Request timeout
        max_retries: Maximum retries
        
    Returns:
        APICallerTool instance
    """
    return APICallerTool(timeout=timeout, max_retries=max_retries)

