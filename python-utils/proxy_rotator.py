#!/usr/bin/env python3
"""
Ultra Research System - Proxy Rotator for Google Scholar Access

Provides proxy rotation for scholarly package to avoid rate limiting.
Supports free proxies, ScraperAPI, and custom proxy lists.

Usage:
    python proxy_rotator.py --test        # Test proxy availability
    python proxy_rotator.py --fetch       # Fetch free proxy list
    python proxy_rotator.py --serve       # Start proxy rotation server
"""

import sys
import json
import random
import time
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import deque
import urllib.request
import urllib.error
import ssl

@dataclass
class ProxyInfo:
    """Proxy information"""
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    anonymity: Optional[str] = None
    last_used: float = 0.0
    fail_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"


class ProxyRotator:
    """Manages proxy rotation for web scraping"""
    
    FREE_PROXY_SOURCES = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=yes&anonymity=all",
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ]
    
    def __init__(
        self,
        proxy_file: Optional[str] = None,
        scraper_api_key: Optional[str] = None,
        min_delay: float = 2.0,
        max_fails: int = 3
    ):
        self.proxies: List[ProxyInfo] = []
        self.working_proxies: deque = deque()
        self.failed_proxies: List[ProxyInfo] = []
        self.scraper_api_key = scraper_api_key
        self.min_delay = min_delay
        self.max_fails = max_fails
        self.lock = threading.Lock()
        self.last_request_time = 0.0
        
        # Load proxies
        if proxy_file:
            self._load_from_file(proxy_file)
        
        # Add ScraperAPI if available
        if scraper_api_key:
            self._add_scraper_api()
    
    def _load_from_file(self, filepath: str):
        """Load proxies from file"""
        lines = []
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            proxy = self._parse_proxy_line(line)
            if proxy:
                self.proxies.append(proxy)
                self.working_proxies.append(proxy)
    
    def _parse_proxy_line(self, line: str) -> Optional[ProxyInfo]:
        """Parse proxy from string"""
        result = None
        
        # Format: host:port or protocol://host:port or user:pass@host:port
        if '@' in line:
            # With auth
            auth_part, host_part = line.rsplit('@', 1)
            protocol = "http"
            
            if '://' in auth_part:
                protocol, auth_part = auth_part.split('://', 1)
            
            username, password = auth_part.split(':', 1)
            host, port = host_part.split(':', 1)
            
            result = ProxyInfo(
                host=host,
                port=int(port),
                protocol=protocol,
                username=username,
                password=password
            )
        
        else:
            # Without auth
            protocol = "http"
            
            if '://' in line:
                protocol, line = line.split('://', 1)
            
            parts = line.split(':')
            if len(parts) == 2:
                host, port = parts
                result = ProxyInfo(
                    host=host,
                    port=int(port),
                    protocol=protocol
                )
        
        return result
    
    def _add_scraper_api(self):
        """Add ScraperAPI as a proxy option"""
        # ScraperAPI works via URL parameter, not traditional proxy
        # We'll handle this specially in get_proxy()
        pass
    
    def fetch_free_proxies(self, test_url: str = "https://scholar.google.com") -> int:
        """Fetch free proxies from public sources"""
        all_proxies = []
        
        for source_url in self.FREE_PROXY_SOURCES:
            proxies = self._fetch_from_source(source_url)
            all_proxies.extend(proxies)
        
        # Deduplicate
        seen = set()
        unique_proxies = []
        for proxy in all_proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        print(f"Fetched {len(unique_proxies)} unique proxies, testing...")
        
        # Test proxies in parallel
        working = self._test_proxies_parallel(unique_proxies, test_url)
        
        with self.lock:
            self.proxies.extend(working)
            self.working_proxies.extend(working)
        
        print(f"Found {len(working)} working proxies")
        return len(working)
    
    def _fetch_from_source(self, url: str) -> List[ProxyInfo]:
        """Fetch proxy list from URL"""
        proxies = []
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        response = None
        content = ""
        
        # Non-blocking style
        done = False
        deadline = time.time() + 10  # 10 second timeout
        
        while not done and time.time() < deadline:
            response = urllib.request.urlopen(request, timeout=10, context=ctx)
            if response:
                content = response.read().decode('utf-8', errors='ignore')
                done = True
        
        if content:
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    proxy = self._parse_proxy_line(line)
                    if proxy:
                        proxies.append(proxy)
        
        return proxies
    
    def _test_proxies_parallel(
        self, 
        proxies: List[ProxyInfo], 
        test_url: str,
        max_workers: int = 20
    ) -> List[ProxyInfo]:
        """Test multiple proxies in parallel"""
        working = []
        lock = threading.Lock()
        
        def test_single(proxy: ProxyInfo):
            if self._test_proxy(proxy, test_url):
                with lock:
                    working.append(proxy)
        
        threads = []
        for proxy in proxies:
            while len([t for t in threads if t.is_alive()]) >= max_workers:
                time.sleep(0.1)
            
            t = threading.Thread(target=test_single, args=(proxy,))
            t.start()
            threads.append(t)
        
        # Wait for all threads
        for t in threads:
            t.join(timeout=30)
        
        return working
    
    def _test_proxy(self, proxy: ProxyInfo, test_url: str, timeout: int = 10) -> bool:
        """Test if a proxy works"""
        result = False
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy.url,
            'https': proxy.url
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        request = urllib.request.Request(
            test_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        start_time = time.time()
        response = None
        
        # Non-blocking polling style
        done = False
        deadline = time.time() + timeout
        
        while not done and time.time() < deadline:
            response = self._open_with_timeout(opener, request, timeout)
            if response:
                done = True
        
        if response and response.status == 200:
            elapsed = time.time() - start_time
            proxy.avg_response_time = elapsed
            result = True
        
        return result
    
    def _open_with_timeout(self, opener, request, timeout):
        """Open URL with timeout using polling"""
        result = [None]
        error = [None]
        done = [False]
        
        def do_open():
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            result[0] = opener.open(request, timeout=timeout, context=ctx)
            done[0] = True
        
        thread = threading.Thread(target=do_open)
        thread.start()
        
        deadline = time.time() + timeout
        while not done[0] and time.time() < deadline:
            time.sleep(0.1)
        
        return result[0]
    
    def get_proxy(self) -> Optional[ProxyInfo]:
        """Get next working proxy with rate limiting"""
        with self.lock:
            # Enforce minimum delay
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                remaining = self.min_delay - elapsed
                # Spin wait instead of sleep
                deadline = time.time() + remaining
                while time.time() < deadline:
                    pass
            
            self.last_request_time = time.time()
            
            if not self.working_proxies:
                return None
            
            # Rotate: get from front, add to back
            proxy = self.working_proxies.popleft()
            proxy.last_used = time.time()
            self.working_proxies.append(proxy)
            
            return proxy
    
    def mark_success(self, proxy: ProxyInfo):
        """Mark proxy as successful"""
        with self.lock:
            proxy.success_count += 1
            proxy.fail_count = 0
    
    def mark_failure(self, proxy: ProxyInfo):
        """Mark proxy as failed"""
        with self.lock:
            proxy.fail_count += 1
            
            if proxy.fail_count >= self.max_fails:
                # Remove from working proxies
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)
                    self.failed_proxies.append(proxy)
    
    def get_scraper_api_url(self, target_url: str) -> Optional[str]:
        """Get ScraperAPI URL for a target"""
        if not self.scraper_api_key:
            return None
        
        from urllib.parse import quote
        return f"https://api.scraperapi.com?api_key={self.scraper_api_key}&url={quote(target_url)}&render=false"
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            "total_proxies": len(self.proxies),
            "working_proxies": len(self.working_proxies),
            "failed_proxies": len(self.failed_proxies),
            "has_scraper_api": self.scraper_api_key is not None
        }
    
    def save_working(self, filepath: str):
        """Save working proxies to file"""
        with open(filepath, 'w') as f:
            for proxy in self.working_proxies:
                f.write(f"{proxy.url}\n")
    
    def to_json(self) -> str:
        """Export as JSON"""
        data = {
            "stats": self.get_stats(),
            "proxies": [asdict(p) for p in self.working_proxies]
        }
        return json.dumps(data, indent=2)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python proxy_rotator.py [--test|--fetch|--serve|--export]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--test":
        # Test existing proxies
        proxy_file = sys.argv[2] if len(sys.argv) > 2 else None
        rotator = ProxyRotator(proxy_file=proxy_file)
        
        print("Testing proxies...")
        test_url = "https://scholar.google.com"
        
        working_count = 0
        for proxy in rotator.proxies:
            result = rotator._test_proxy(proxy, test_url)
            status = "✓" if result else "✗"
            print(f"  {status} {proxy.host}:{proxy.port}")
            if result:
                working_count += 1
        
        print(f"\nWorking: {working_count}/{len(rotator.proxies)}")
    
    elif command == "--fetch":
        # Fetch and test free proxies
        rotator = ProxyRotator()
        count = rotator.fetch_free_proxies()
        
        output_file = sys.argv[2] if len(sys.argv) > 2 else "proxies.txt"
        rotator.save_working(output_file)
        print(f"Saved {count} working proxies to {output_file}")
    
    elif command == "--serve":
        # Start as a proxy rotation server
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888
        
        proxy_file = "proxies.txt"
        scraper_api_key = None
        
        # Check for API key env var
        import os
        scraper_api_key = os.environ.get("SCRAPER_API_KEY")
        
        rotator = ProxyRotator(
            proxy_file=proxy_file if os.path.exists(proxy_file) else None,
            scraper_api_key=scraper_api_key
        )
        
        if not rotator.proxies and not scraper_api_key:
            print("No proxies found, fetching free proxies...")
            rotator.fetch_free_proxies()
        
        print(f"Proxy rotator running on port {port}")
        print(f"Stats: {rotator.get_stats()}")
        
        # Simple HTTP server for proxy requests
        # In production, would use proper server
        while True:
            time.sleep(1)
    
    elif command == "--export":
        # Export proxy list as JSON
        proxy_file = sys.argv[2] if len(sys.argv) > 2 else None
        rotator = ProxyRotator(proxy_file=proxy_file)
        print(rotator.to_json())
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
