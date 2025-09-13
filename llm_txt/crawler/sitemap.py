"""Sitemap discovery and parsing for efficient crawling."""

import logging
import xml.etree.ElementTree as ET
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class SitemapParser:
    """Discovers and parses XML sitemaps to find URLs to crawl."""
    
    def __init__(self, user_agent: str = "llm-txt-generator/0.1.0") -> None:
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
    
    def discover_urls(self, base_url: str) -> Set[str]:
        """Discover URLs from sitemap(s) at the given base URL."""
        urls: Set[str] = set()
        
        # Try common sitemap locations
        sitemap_urls = self._find_sitemaps(base_url)
        
        for sitemap_url in sitemap_urls:
            try:
                sitemap_urls_found = self._parse_sitemap(sitemap_url)
                urls.update(sitemap_urls_found)
                logger.info(f"Found {len(sitemap_urls_found)} URLs in sitemap: {sitemap_url}")
            except Exception as e:
                logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    def _find_sitemaps(self, base_url: str) -> List[str]:
        """Find sitemap URLs for a domain."""
        sitemaps = []
        
        # Check robots.txt for sitemap declarations
        robots_sitemaps = self._get_sitemaps_from_robots(base_url)
        sitemaps.extend(robots_sitemaps)
        
        # Try common sitemap locations
        common_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemaps.xml",
            "/sitemap/sitemap.xml"
        ]
        
        for path in common_paths:
            sitemap_url = urljoin(base_url, path)
            if sitemap_url not in sitemaps and self._url_exists(sitemap_url):
                sitemaps.append(sitemap_url)
        
        return sitemaps
    
    def _get_sitemaps_from_robots(self, base_url: str) -> List[str]:
        """Extract sitemap URLs from robots.txt."""
        sitemaps = []
        robots_url = urljoin(base_url, "/robots.txt")
        
        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        sitemaps.append(sitemap_url)
        except RequestException as e:
            logger.debug(f"Could not fetch robots.txt from {robots_url}: {e}")
        
        return sitemaps
    
    def _url_exists(self, url: str) -> bool:
        """Check if a URL exists (returns 200)."""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except RequestException:
            return False
    
    def _parse_sitemap(self, sitemap_url: str) -> Set[str]:
        """Parse an XML sitemap and extract URLs."""
        urls: Set[str] = set()
        
        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            # Check if the response is actually XML
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type or response.text.strip().startswith('<!DOCTYPE') or response.text.strip().startswith('<html'):
                logger.warning(f"Sitemap URL {sitemap_url} returned HTML instead of XML. Sitemap may be blocked or unavailable.")
                return urls
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle different sitemap formats
            if self._is_sitemap_index(root):
                # This is a sitemap index, parse each referenced sitemap
                sitemap_urls = self._parse_sitemap_index(root)
                for sub_sitemap_url in sitemap_urls:
                    sub_urls = self._parse_sitemap(sub_sitemap_url)
                    urls.update(sub_urls)
            else:
                # This is a regular sitemap with URLs
                urls.update(self._parse_url_sitemap(root))
                
        except ET.ParseError as e:
            # Check if this might be an HTML page
            if sitemap_url:
                logger.warning(f"Failed to parse sitemap at {sitemap_url} - may be blocked or returning HTML")
        except RequestException as e:
            logger.error(f"Network error fetching sitemap {sitemap_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing sitemap {sitemap_url}: {e}")
        
        return urls
    
    def _is_sitemap_index(self, root: ET.Element) -> bool:
        """Check if this is a sitemap index file."""
        # Check for sitemapindex root element
        if root.tag.endswith("sitemapindex"):
            return True
        
        # Check for sitemap children
        for child in root:
            if child.tag.endswith("sitemap"):
                return True
        
        return False
    
    def _parse_sitemap_index(self, root: ET.Element) -> List[str]:
        """Parse a sitemap index and return sitemap URLs."""
        sitemap_urls = []
        
        for sitemap in root:
            if sitemap.tag.endswith("sitemap"):
                for child in sitemap:
                    if child.tag.endswith("loc"):
                        sitemap_urls.append(child.text.strip())
        
        return sitemap_urls
    
    def _parse_url_sitemap(self, root: ET.Element) -> Set[str]:
        """Parse a URL sitemap and return page URLs."""
        urls: Set[str] = set()
        
        for url_elem in root:
            if url_elem.tag.endswith("url"):
                for child in url_elem:
                    if child.tag.endswith("loc"):
                        url = child.text.strip()
                        if self._is_valid_url(url):
                            urls.add(url)
        
        return urls
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and parsed.netloc
        except Exception:
            return False