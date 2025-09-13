"""Async web crawler implementation."""

import asyncio
import logging
import time
from typing import List, Set, Optional, Dict, Any
import re
from urllib.parse import urljoin, urlparse
import aiohttp
from aiohttp import ClientError, ClientTimeout
from bs4 import BeautifulSoup
import html2text

from .models import CrawlConfig, PageContent, CrawlResult
from .robots import RobotsChecker
from .sitemap import SitemapParser

logger = logging.getLogger(__name__)


class AsyncWebCrawler:
    """Async web crawler for extracting content from documentation sites."""
    
    def __init__(self, config: Optional[CrawlConfig] = None, progress_callback=None) -> None:
        self.config = config or CrawlConfig()
        self.progress_callback = progress_callback
        self.robots_checker = RobotsChecker(self.config.user_agent)
        self.sitemap_parser = SitemapParser(self.config.user_agent)
        self.headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }
        
        # Initialize HTML to markdown converter
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.ignore_emphasis = False
        self.html2text.body_width = 0
        self.html2text.unicode_snob = True
    
    async def crawl(self, start_url: str) -> CrawlResult:
        """Crawl a website starting from the given URL."""
        start_time = time.time()
        logger.info(f"Starting async crawl from {start_url}")
        
        # Create session with timeout
        timeout = ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
            # Discover URLs from sitemap (still sync for now)
            discovered_urls = self.sitemap_parser.discover_urls(start_url)
            
            # If sitemap failed, use fallback
            if not discovered_urls:
                logger.warning(f"No sitemap found for {start_url}. Using fallback strategy.")
                discovered_urls = await self._fallback_url_discovery(session, start_url)
            
            # Always include start URL
            discovered_urls.add(start_url)
            logger.info(f"Total URLs discovered: {len(discovered_urls)}")
            
            # Filter and organize URLs
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
                
                # Process URLs at this depth with limited concurrency
                tasks = []
                for url in depth_urls:
                    if len(pages) >= self.config.max_pages:
                        break
                    
                    # Check robots.txt
                    if self.config.respect_robots and not self.robots_checker.can_fetch(url):
                        logger.info(f"Blocked by robots.txt: {url}")
                        blocked_urls.append(url)
                        continue
                    
                    # Add to tasks for concurrent processing
                    tasks.append(self._fetch_page(session, url, depth))
                
                # Process tasks with concurrency limit
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Error crawling page: {result}")
                            failed_urls.append(str(result))
                        elif result:
                            pages.append(result)
                            if self.progress_callback:
                                self.progress_callback(result.url, len(pages), len(discovered_urls))
                        
                        if len(pages) >= self.config.max_pages:
                            break
                
                # Small delay between depths
                if depth < self.config.max_depth:
                    await asyncio.sleep(self.config.request_delay)
        
        duration = time.time() - start_time
        
        return CrawlResult(
            pages=pages,
            failed_urls=failed_urls,
            blocked_urls=blocked_urls,
            total_pages=len(pages),
            success_rate=0.0,  # Calculated in __post_init__
            duration=duration
        )
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str, depth: int) -> Optional[PageContent]:
        """Fetch and extract content from a single page."""
        try:
            async with session.get(url, allow_redirects=self.config.follow_redirects) as response:
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    logger.debug(f"Skipping non-HTML content: {url} ({content_type})")
                    return None
                
                # Read content
                html = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html, 'lxml')

                # Language filter: prefer English pages
                if self.config.language and self.config.language.startswith('en'):
                    lang_attr = (soup.html.get('lang') if soup.html else None) or ''
                    header_lang = response.headers.get('Content-Language', '')
                    page_lang = (lang_attr or header_lang).lower()
                    if page_lang and not page_lang.startswith('en'):
                        logger.info(f"Skipping non-English page {url} (lang={page_lang})")
                        return None
                
                # Extract title
                title_elem = soup.find('title')
                title = title_elem.get_text().strip() if title_elem else ""
                
                # Clean soup
                self._clean_soup(soup)
                
                # Extract main content
                content_html = self._extract_main_content(soup)
                
                # Convert to markdown
                markdown = self.html2text.handle(str(content_html)).strip()
                
                # Extract plain text
                content_text = soup.get_text(separator=' ', strip=True)
                
                # Extract links
                links = self._extract_links(soup, url)
                
                # Metadata
                metadata = {
                    'word_count': len(content_text.split()),
                    'char_count': len(content_text),
                    'markdown_length': len(markdown),
                    'final_url': str(response.url)
                }
                
                return PageContent(
                    url=url,
                    title=title,
                    content=content_text,
                    markdown=markdown,
                    depth=depth,
                    timestamp=time.time(),
                    status_code=response.status,
                    content_type=content_type,
                    links=links,
                    metadata=metadata
                )
        
        except ClientError as e:
            logger.warning(f"Network error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    async def _fallback_url_discovery(self, session: aiohttp.ClientSession, start_url: str) -> Set[str]:
        """Fallback URL discovery when sitemap is not available."""
        discovered_urls: Set[str] = set()
        
        try:
            parsed_base = urlparse(start_url)
            base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
            
            # Common documentation paths
            common_doc_paths = [
                '/docs', '/documentation', '/api', '/reference',
                '/guide', '/tutorial', '/getting-started', '/quickstart',
                '/api-reference', '/api-docs', '/developer', '/examples'
            ]
            
            # Add common paths
            for path in common_doc_paths:
                full = urljoin(base_domain, path)
                if not self._should_skip_url_for_language(urlparse(full).path):
                    discovered_urls.add(full)
            
            # Fetch start page and extract links
            logger.info(f"Discovering URLs from page content at {start_url}")
            
            async with session.get(start_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find documentation links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(start_url, href)
                        
                        parsed_url = urlparse(absolute_url)
                        if parsed_url.netloc == parsed_base.netloc:
                            url_lower = absolute_url.lower()
                            doc_keywords = ['doc', 'api', 'guide', 'tutorial', 'reference',
                                          'manual', 'help', 'example', 'getting-started']
                            
                            if any(keyword in url_lower for keyword in doc_keywords):
                                if not self._should_skip_url_for_language(urlparse(absolute_url).path):
                                    discovered_urls.add(absolute_url)
                    
                    logger.info(f"Discovered {len(discovered_urls)} URLs through fallback")
        
        except Exception as e:
            logger.error(f"Error in fallback URL discovery: {e}")
        
        return discovered_urls
    
    def _organize_urls_by_depth(self, start_url: str, urls: Set[str]) -> Dict[int, List[str]]:
        """Organize URLs by their depth from the start URL."""
        parsed_start = urlparse(start_url)
        start_path_parts = [p for p in parsed_start.path.split('/') if p]
        
        depth_urls: Dict[int, List[str]] = {}
        
        for url in urls:
            if self._is_non_html_url(url):
                continue
            
            parsed_url = urlparse(url)
            if parsed_url.netloc != parsed_start.netloc:
                continue
            # Language filter: skip obvious non-English locales in path if configured
            if self._should_skip_url_for_language(parsed_url.path):
                continue
            
            path_parts = [p for p in parsed_url.path.split('/') if p]
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
    
    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from the parsed HTML."""
        unwanted_tags = ['script', 'style', 'nav', 'footer', 'aside', 'header']
        unwanted_classes = ['nav', 'navigation', 'menu', 'sidebar', 'footer', 'header', 'breadcrumb']
        unwanted_ids = ['nav', 'navigation', 'menu', 'sidebar', 'footer', 'header', 'breadcrumb']
        
        # Remove by tag
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
        """Extract the main content area from the page."""
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '[role="main"]',
            '.main-content', '.content', '.documentation',
            '#main', '#content', '#documentation'
        ]
        
        for selector in main_selectors:
            content = soup.select_one(selector)
            if content:
                return content
        
        # Fallback to body
        return soup.find('body') or soup
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        return links

    def _should_skip_url_for_language(self, path: str) -> bool:
        """Heuristically skip non-English locale paths when language is set to 'en'.

        Looks at early path segments like '/zh', '/zh-TW', '/fr', '/ja', '/pt-br', etc.
        """
        if not self.config.language or self.config.language.lower().startswith('en') is False:
            # Only enforce when requesting English
            return False
        segments = [seg.lower() for seg in path.split('/') if seg]
        if not segments:
            return False
        locale = segments[0]
        # Match i18n locale patterns
        if re.fullmatch(r"[a-z]{2}([-_][a-z]{2,4})?", locale):
            # Allow 'en', 'en-us', 'en_gb'
            if locale.startswith('en'):
                return False
            return True
        return False
