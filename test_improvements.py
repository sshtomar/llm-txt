#!/usr/bin/env python3
"""
Test script for validating the comprehensive improvements to llm.txt generation.
"""
import asyncio
import logging
from llm_txt.crawler import WebCrawler, CrawlConfig
from llm_txt.composer.composer import LLMTxtComposer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_improvements():
    """Test the improved llm.txt generation."""
    
    # Test URL - using a simple documentation page
    test_url = "https://docs.python.org/3/library/json.html"
    
    logger.info(f"Testing with URL: {test_url}")
    
    # Configure crawler with improved settings
    config = CrawlConfig(
        max_pages=10,  # Small for testing
        max_depth=2,   # Limited depth for quick test
        request_delay=0.5,
        respect_robots=True
    )
    
    # Create crawler
    crawler = WebCrawler(config)
    
    # Crawl the site
    logger.info("Starting crawl...")
    result = crawler.crawl(test_url)
    
    logger.info(f"Crawled {len(result.pages)} pages")
    
    if not result.pages:
        logger.error("No pages crawled!")
        return
    
    # Create composer
    composer = LLMTxtComposer()
    
    # Generate llm.txt
    logger.info("Generating llm.txt...")
    llm_txt = await composer.compose_llm_txt(result.pages)
    
    # Save output for inspection
    output_file = "test_output.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(llm_txt)
    
    # Validate output quality
    is_valid, issues = composer._validate_output_quality(llm_txt)
    
    # Report results
    logger.info("="*50)
    logger.info("TEST RESULTS:")
    logger.info(f"Pages crawled: {len(result.pages)}")
    logger.info(f"Output size: {len(llm_txt)} chars ({len(llm_txt.encode('utf-8'))/1024:.1f} KB)")
    logger.info(f"Quality validation: {'PASSED' if is_valid else 'FAILED'}")
    
    if not is_valid:
        logger.warning("Quality issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    logger.info(f"Output saved to: {output_file}")
    logger.info("="*50)
    
    # Show first 500 chars of output
    logger.info("First 500 characters of output:")
    print(llm_txt[:500])

if __name__ == "__main__":
    asyncio.run(test_improvements())