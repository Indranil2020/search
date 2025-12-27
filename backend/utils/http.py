"""
HTTP Client with Result Pattern

All operations return Result types.
Exception handling only at boundary layer for external libraries.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any
from dataclasses import dataclass
import ssl
import socket

from .result import Result, Ok, Err, boundary_call
from .rate_limiter import RateLimiter


@dataclass
class HttpResponse:
    """HTTP response container."""
    status_code: int
    body: str
    headers: Dict[str, str]
    url: str
    
    def json(self) -> Result[Dict, str]:
        """Parse body as JSON."""
        return parse_json(self.body)
    
    def xml(self) -> Result[ET.Element, str]:
        """Parse body as XML."""
        return parse_xml(self.body)


@dataclass
class HttpError:
    """HTTP error details."""
    message: str
    status_code: Optional[int] = None
    url: Optional[str] = None


class HttpClient:
    """HTTP client returning Result types."""
    
    def __init__(
        self,
        timeout: int = 30,
        rate_limit: float = 10.0,
        user_agent: str = "SearchSystem/1.0"
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.limiter = RateLimiter(rate_limit)
        self.ssl_ctx = ssl.create_default_context()
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Result[HttpResponse, HttpError]:
        """GET request returning Result."""
        
        # Validate URL
        if not url or not isinstance(url, str):
            return Err(HttpError("Invalid URL"))
        
        if not url.startswith(('http://', 'https://')):
            return Err(HttpError("URL must start with http:// or https://"))
        
        # Add query params
        if params:
            query = urllib.parse.urlencode(params)
            sep = '&' if '?' in url else '?'
            url = f"{url}{sep}{query}"
        
        return self._execute("GET", url, headers, None)
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        as_json: bool = True
    ) -> Result[HttpResponse, HttpError]:
        """POST request returning Result."""
        
        if not url or not isinstance(url, str):
            return Err(HttpError("Invalid URL"))
        
        if not url.startswith(('http://', 'https://')):
            return Err(HttpError("URL must start with http:// or https://"))
        
        body = None
        hdrs = dict(headers) if headers else {}
        
        if data:
            if as_json:
                body = json.dumps(data).encode('utf-8')
                hdrs['Content-Type'] = 'application/json'
            else:
                body = urllib.parse.urlencode(data).encode('utf-8')
                hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
        
        return self._execute("POST", url, hdrs, body)
    
    def _execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        body: Optional[bytes]
    ) -> Result[HttpResponse, HttpError]:
        """Execute request with Result return."""
        
        # Rate limit
        self.limiter.wait()
        
        # Build headers
        hdrs = {"User-Agent": self.user_agent}
        if headers:
            hdrs.update(headers)
        
        # Build request
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self.ssl_ctx)
        )
        
        # Execute at boundary layer
        return self._boundary_execute(opener, req, url)
    
    def _boundary_execute(
        self,
        opener,
        req,
        url: str
    ) -> Result[HttpResponse, HttpError]:
        """Boundary layer - handle external library exceptions."""
        
        # This is the ONLY exception handling in the HTTP client
        # urllib is exception-based, we convert here
        
        resp = None
        error_result = None
        
        # Boundary: urllib exceptions converted to Result
        try:
            resp = opener.open(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            return Err(HttpError(f"HTTP {e.code}: {e.reason}", e.code, url))
        except urllib.error.URLError as e:
            return Err(HttpError(f"Connection failed: {e.reason}", url=url))
        except socket.timeout:
            return Err(HttpError("Request timed out", url=url))
        except socket.error as e:
            return Err(HttpError(f"Network error: {e}", url=url))
        except ssl.SSLError as e:
            return Err(HttpError(f"SSL error: {e}", url=url))
        except Exception as e:
            return Err(HttpError(f"Request error: {e}", url=url))
        
        # Read response
        body = ""
        if resp:
            raw = resp.read()
            if raw:
                body = raw.decode('utf-8', errors='replace')
            resp.close()
        
        return Ok(HttpResponse(
            status_code=resp.status if resp else 0,
            body=body,
            headers=dict(resp.headers) if resp and hasattr(resp, 'headers') else {},
            url=url
        ))


def parse_json(text: str) -> Result[Dict, str]:
    """Parse JSON with Result return."""
    
    if not text or not isinstance(text, str):
        return Err("Empty input")
    
    text = text.strip()
    if not text:
        return Err("Empty string")
    
    # Validate format before parsing
    if not (text.startswith('{') or text.startswith('[')):
        return Err("Invalid JSON format")
    
    # Boundary: json module exceptions
    try:
        return Ok(json.loads(text))
    except json.JSONDecodeError as e:
        return Err(f"JSON parse error: {e.msg}")
    except Exception as e:
        return Err(f"Parse error: {e}")


def parse_xml(text: str) -> Result[ET.Element, str]:
    """Parse XML with Result return."""
    
    if not text or not isinstance(text, str):
        return Err("Empty input")
    
    text = text.strip()
    if not text:
        return Err("Empty string")
    
    if not text.startswith('<'):
        return Err("Invalid XML format")
    
    # Boundary: xml module exceptions
    try:
        return Ok(ET.fromstring(text))
    except ET.ParseError as e:
        return Err(f"XML parse error: {e}")
    except Exception as e:
        return Err(f"Parse error: {e}")
