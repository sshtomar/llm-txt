"""Main web crawler implementation."""

import asyncio
import logging
import time
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, urlencode
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import html2text

from .models import CrawlConfig, PageContent, CrawlResult
from .robots import RobotsChecker
from .sitemap import SitemapParser

logger = logging.getLogger(__name__)


class WebCrawler:
    """Web crawler for extracting content from documentation sites."""
    
    def __init__(self, config: Optional[CrawlConfig] = None) -> None:
        self.config = config or CrawlConfig()
        self.robots_checker = RobotsChecker(self.config.user_agent)
        self.sitemap_parser = SitemapParser(self.config.user_agent)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        })
        
        # Initialize HTML to markdown converter
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.ignore_emphasis = False
        self.html2text.body_width = 0  # No line wrapping
        self.html2text.unicode_snob = True
    
    def crawl(self, start_url: str) -> CrawlResult:
        """Crawl a website starting from the given URL."""
        start_time = time.time()
        
        logger.info(f"Starting crawl from {start_url}")
        
        # Discover URLs from sitemap
        discovered_urls = self.sitemap_parser.discover_urls(start_url)
        
        # Add start URL if not in sitemap
        if start_url not in discovered_urls:
            discovered_urls.add(start_url)
        
        # Filter URLs and organize by depth
        urls_to_crawl = self._organize_urls_by_depth(start_url, discovered_urls)
        
        # Crawl pages
        pages = []
        failed_urls = []
        blocked_urls = []
        
        for depth in range(min(self.config.max_depth + 1, len(urls_to_crawl))):
            if len(pages) >= self.config.max_pages:
                break
                
            depth_urls = urls_to_crawl.get(depth, [])
            logger.info(f"Crawling depth {depth}: {len(depth_urls)} URLs")
            
            for url in depth_urls:
                if len(pages) >= self.config.max_pages:
                    break
                
                # Check robots.txt
                if self.config.respect_robots and not self.robots_checker.can_fetch(url):
                    logger.info(f"Blocked by robots.txt: {url}")
                    blocked_urls.append(url)
                    continue
                
                # Fetch page
                page_content = self._fetch_page(url, depth)
                if page_content:
                    pages.append(page_content)
                    logger.debug(f"Successfully crawled: {url}")
                else:
                    failed_urls.append(url)
                    logger.warning(f"Failed to crawl: {url}")
                
                # Respect crawl delay
                self._respect_crawl_delay(url)
        
        duration = time.time() - start_time
        
        return CrawlResult(
            pages=pages,
            failed_urls=failed_urls,
            blocked_urls=blocked_urls,
            total_pages=len(pages),
            success_rate=0.0,  # Will be calculated in __post_init__
            duration=duration
        )
    
    def _organize_urls_by_depth(self, start_url: str, urls: Set[str]) -> Dict[int, List[str]]:
        """Organize URLs by their depth from the start URL."""
        start_parsed = urlparse(start_url)
        start_path_parts = [p for p in start_parsed.path.split('/') if p]
        
        depth_urls: Dict[int, List[str]] = {}
        
        for url in urls:
            # Only include URLs from the same domain
            parsed = urlparse(url)
            if parsed.netloc != start_parsed.netloc:
                continue
            
            # Skip non-HTML URLs
            if self._is_non_html_url(url):
                continue
            
            # Calculate depth based on path difference
            path_parts = [p for p in parsed.path.split('/') if p]
            depth = max(0, len(path_parts) - len(start_path_parts))
            
            if depth not in depth_urls:
                depth_urls[depth] = []
            depth_urls[depth].append(url)
        
        # Sort URLs within each depth
        for depth in depth_urls:
            depth_urls[depth].sort()
        
        return depth_urls
    
    def _is_non_html_url(self, url: str) -> bool:
        """Check if URL is likely not an HTML page."""
        non_html_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            '.css', '.js', '.json', '.xml', '.txt'
        }
        
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        
        return any(path_lower.endswith(ext) for ext in non_html_extensions)
    
    def _fetch_page(self, url: str, depth: int) -> Optional[PageContent]:
        """Fetch and extract content from a single page."""
        try:
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=self.config.follow_redirects
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url} ({content_type})")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Remove unwanted elements
            self._clean_soup(soup)
            
            # Extract main content
            content_html = self._extract_main_content(soup)
            
            # Convert to markdown
            markdown = self.html2text.handle(str(content_html)).strip()
            
            # Extract plain text for content
            content_text = soup.get_text(separator=' ', strip=True)
            
            # Find links
            links = self._extract_links(soup, url)
            
            # Create metadata
            metadata = {
                'word_count': len(content_text.split()),
                'char_count': len(content_text),
                'markdown_length': len(markdown),
                'final_url': response.url
            }
            
            return PageContent(
                url=url,
                title=title,
                content=content_text,
                markdown=markdown,
                depth=depth,
                timestamp=time.time(),
                status_code=response.status_code,
                content_type=content_type,
                links=links,
                metadata=metadata
            )
            
        except RequestException as e:
            logger.warning(f"Network error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from the parsed HTML."""
        # Remove script, style, nav, footer, sidebar elements
        unwanted_tags = ['script', 'style', 'nav', 'footer', 'aside', 'header']
        unwanted_classes = ['nav', 'navigation', 'menu', 'sidebar', 'footer', 'header', 'breadcrumb']
        unwanted_ids = ['nav', 'navigation', 'menu', 'sidebar', 'footer', 'header', 'breadcrumb']
        
        # Remove by tag name
        for tag_name in unwanted_tags:
            for element in soup.find_all(tag_name):
                element.decompose()
        
        # Remove by class
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=lambda x: x and class_name in ' '.join(x).lower()):
                element.decompose()
        
        # Remove by id
        for id_name in unwanted_ids:
            for element in soup.find_all(id=lambda x: x and id_name in x.lower()):
                element.decompose()
    
    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract the main content from the page."""
        # Try to find main content containers
        main_selectors = [
            'main',
            '[role="main"]',
            '.main',
            '.content',
            '.main-content',
            '.page-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'article',
            '.documentation'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content
        
        # If no main content found, use body
        body = soup.find('body')
        return body if body else soup
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and resolve links from the page."""
        links = []
        
        for link_elem in soup.find_all('a', href=True):
            href = link_elem['href'].strip()
            if href:
                absolute_url = urljoin(base_url, href)
                # Only include HTTP(S) links
                if absolute_url.startswith(('http://', 'https://')):
                    links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def _respect_crawl_delay(self, url: str) -> None:
        """Respect crawl delay from robots.txt or configuration."""
        if self.config.respect_robots:
            robots_delay = self.robots_checker.get_crawl_delay(url)
            delay = max(self.config.request_delay, robots_delay or 0)
        else:
            delay = self.config.request_delay
        
        if delay > 0:
            time.sleep(delay)