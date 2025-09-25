"""Command-line interface for the LLM-TXT generator."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import click
from dotenv import load_dotenv

from ..crawler import WebCrawler, CrawlConfig
from ..composer import LLMTxtComposer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli() -> None:
    """LLM-TXT Generator - Convert documentation URLs to LLM-friendly summaries."""
    pass


@cli.command()
@click.option('--url', required=True, help='URL of the documentation site to crawl')
@click.option('--output', '-o', default='llm.txt', help='Output filename for the generated content')
@click.option('--full', is_flag=True, help='Generate full version (llms-full.txt)')
@click.option('--max-pages', default=100, help='Maximum pages to crawl')
@click.option('--max-depth', default=3, help='Maximum crawl depth')
@click.option('--max-kb', default=500, help='Maximum size in KB for llm.txt')
@click.option('--no-robots', is_flag=True, help='Ignore robots.txt')
@click.option('--delay', default=1.0, help='Request delay in seconds')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(
    url: str,
    output: str,
    full: bool,
    max_pages: int,
    max_depth: int,
    max_kb: int,
    no_robots: bool,
    delay: float,
    verbose: bool
) -> None:
    """Generate llm.txt from a documentation URL."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    asyncio.run(_generate_async(
        url=url,
        output=output,
        full=full,
        max_pages=max_pages,
        max_depth=max_depth,
        max_kb=max_kb,
        respect_robots=not no_robots,
        delay=delay
    ))


async def _generate_async(
    url: str,
    output: str,
    full: bool,
    max_pages: int,
    max_depth: int,
    max_kb: int,
    respect_robots: bool,
    delay: float
) -> None:
    """Async implementation of generate command."""
    try:
        click.echo(f"Starting generation for: {url}")
        
        # Configure crawler
        config = CrawlConfig(
            max_pages=max_pages,
            max_depth=max_depth,
            request_delay=delay,
            respect_robots=respect_robots
        )
        
        # Initialize crawler and composer
        crawler = WebCrawler(config)
        composer = LLMTxtComposer(max_kb=max_kb)
        
        click.echo(f"Crawling with max_pages={max_pages}, max_depth={max_depth}")
        
        # Crawl the site
        crawl_result = await crawler.crawl(url)
        
        if not crawl_result.pages:
            click.echo("❌ No pages could be crawled. Check the URL and try again.")
            sys.exit(1)
        
        click.echo(f"✅ Crawled {len(crawl_result.pages)} pages successfully")
        
        if crawl_result.failed_urls:
            click.echo(f"⚠️ {len(crawl_result.failed_urls)} URLs failed to crawl")
        
        if crawl_result.blocked_urls:
            click.echo(f"🚫 {len(crawl_result.blocked_urls)} URLs blocked by robots.txt")
        
        # Generate content
        click.echo("Generating llm.txt content...")
        
        llm_txt_content = await composer.compose_llm_txt(crawl_result.pages)
        
        # Write to file
        output_path = Path(output)
        output_path.write_text(llm_txt_content, encoding='utf-8')
        
        size_kb = len(llm_txt_content.encode('utf-8')) / 1024
        click.echo(f"✅ Generated {output} ({size_kb:.1f}KB)")
        
        # Generate full version if requested
        if full:
            full_output = output_path.with_suffix('.full.txt')
            click.echo("Generating full version...")
            
            full_content = await composer.compose_llms_full_txt(crawl_result.pages)
            full_output.write_text(full_content, encoding='utf-8')
            
            full_size_kb = len(full_content.encode('utf-8')) / 1024
            click.echo(f"✅ Generated {full_output} ({full_size_kb:.1f}KB)")
        
        # Show summary
        click.echo(f"""
📊 Generation Summary:
   • Pages crawled: {len(crawl_result.pages)}
   • Success rate: {crawl_result.success_rate:.1%}
   • Duration: {crawl_result.duration:.1f}s
   • Output size: {size_kb:.1f}KB
        """)
        
    except KeyboardInterrupt:
        click.echo("\n❌ Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Generation failed: {e}")
        logger.error(f"Generation failed: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()