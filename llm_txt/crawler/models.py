"""Data models for crawler module."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
import time


@dataclass
class CrawlConfig:
    """Configuration for web crawling."""
    
    max_pages: int = 150
    max_depth: int = 5
    request_delay: float = 1.0
    user_agent: str = "llm-txt-generator/0.1.0"
    respect_robots: bool = True
    timeout: int = 30
    follow_redirects: bool = True
    # Preferred language (used to filter locale-specific pages)
    # Example: "en" to prefer English content only
    language: Optional[str] = "en"


@dataclass
class PageContent:
    """Represents extracted content from a web page."""
    
    url: str
    title: str
    content: str
    markdown: str
    depth: int
    timestamp: float
    status_code: int
    content_type: str
    links: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class CrawlResult:
    """Result of a crawling operation."""
    
    pages: List[PageContent]
    failed_urls: List[str]
    blocked_urls: List[str]
    total_pages: int
    success_rate: float
    duration: float
    
    def __post_init__(self) -> None:
        self.total_pages = len(self.pages)
        if self.total_pages > 0:
            self.success_rate = self.total_pages / (self.total_pages + len(self.failed_urls))
        else:
            self.success_rate = 0.0
