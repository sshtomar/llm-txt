"""Robots.txt checker for respecting crawling policies."""

import logging
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Handles robots.txt checking and caching."""
    
    def __init__(self, user_agent: str = "llm-txt-generator/0.1.0") -> None:
        self.user_agent = user_agent
        self._cache: Dict[str, RobotFileParser] = {}
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get or create robots parser for this domain
            if base_url not in self._cache:
                self._cache[base_url] = self._load_robots_txt(base_url)
            
            robots_parser = self._cache[base_url]
            if robots_parser is None:
                # No robots.txt found, assume allowed
                return True
            
            return robots_parser.can_fetch(self.user_agent, url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # On error, be conservative and allow
            return True
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """Get crawl delay from robots.txt if specified."""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url not in self._cache:
                self._cache[base_url] = self._load_robots_txt(base_url)
            
            robots_parser = self._cache[base_url]
            if robots_parser is None:
                return None
            
            delay = robots_parser.crawl_delay(self.user_agent)
            return float(delay) if delay is not None else None
            
        except Exception as e:
            logger.warning(f"Error getting crawl delay for {url}: {e}")
            return None
    
    def _load_robots_txt(self, base_url: str) -> Optional[RobotFileParser]:
        """Load and parse robots.txt for a domain."""
        robots_url = urljoin(base_url, "/robots.txt")
        
        try:
            logger.debug(f"Fetching robots.txt from {robots_url}")
            response = requests.get(
                robots_url,
                timeout=10,
                headers={"User-Agent": self.user_agent}
            )
            
            if response.status_code == 200:
                robots_parser = RobotFileParser()
                robots_parser.set_url(robots_url)
                robots_parser.read()
                
                # Manual parsing since set_url + read doesn't work with string content
                lines = response.text.splitlines()
                robots_parser.parse(lines)
                
                logger.debug(f"Successfully loaded robots.txt for {base_url}")
                return robots_parser
            
            elif response.status_code == 404:
                logger.debug(f"No robots.txt found for {base_url}")
                return None
            
            else:
                logger.warning(f"Failed to fetch robots.txt from {robots_url}: {response.status_code}")
                return None
                
        except RequestException as e:
            logger.warning(f"Network error fetching robots.txt from {robots_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading robots.txt from {robots_url}: {e}")
            return None