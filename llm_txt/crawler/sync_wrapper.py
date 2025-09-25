"""Synchronous wrapper for the async WebCrawler."""

import asyncio
from typing import Optional
from .async_crawler import WebCrawler as AsyncWebCrawler
from .models import CrawlConfig, CrawlResult


class WebCrawlerSync:
    """Synchronous wrapper for WebCrawler to use in CLI."""

    def __init__(self, config: Optional[CrawlConfig] = None):
        self.async_crawler = AsyncWebCrawler(config)
        self.config = config

    def crawl(self, start_url: str) -> CrawlResult:
        """Synchronously crawl a website."""
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, create a new loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.async_crawler.crawl(start_url))
                finally:
                    loop.close()
            else:
                return loop.run_until_complete(self.async_crawler.crawl(start_url))
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.async_crawler.crawl(start_url))