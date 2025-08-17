"""Tests for the web crawler module."""

import pytest
from llm_txt.crawler import WebCrawler, CrawlConfig
from llm_txt.crawler.robots import RobotsChecker
from llm_txt.crawler.sitemap import SitemapParser


def test_crawl_config_defaults():
    """Test default configuration values."""
    config = CrawlConfig()
    assert config.max_pages == 100
    assert config.max_depth == 3
    assert config.request_delay == 1.0
    assert config.respect_robots is True


def test_robots_checker_init():
    """Test robots checker initialization."""
    checker = RobotsChecker("test-agent/1.0")
    assert checker.user_agent == "test-agent/1.0"


def test_sitemap_parser_init():
    """Test sitemap parser initialization."""
    parser = SitemapParser("test-agent/1.0")
    assert parser.user_agent == "test-agent/1.0"


def test_web_crawler_init():
    """Test web crawler initialization."""
    config = CrawlConfig(max_pages=50, user_agent="test-crawler/1.0")
    crawler = WebCrawler(config)
    assert crawler.config.max_pages == 50
    assert crawler.config.user_agent == "test-crawler/1.0"


@pytest.mark.integration
def test_crawl_simple_page():
    """Integration test for crawling a simple page."""
    # This would be a real integration test
    # For now, just test that we can create a crawler
    config = CrawlConfig(max_pages=1, max_depth=1)
    crawler = WebCrawler(config)
    assert crawler is not None