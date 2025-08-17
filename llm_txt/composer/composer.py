"""Composer for generating LLM-friendly text summaries."""

import os
import logging
from typing import List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from ..crawler.models import PageContent

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMTxtComposer:
    """Composes llm.txt content from crawled pages using Anthropic Claude."""
    
    def __init__(self, api_key: Optional[str] = None, max_kb: int = 500) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.max_kb = max_kb
        self.client = None
        
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            logger.warning("No Anthropic API key provided. Composer will use basic text processing.")
    
    async def compose_llm_txt(self, pages: List[PageContent]) -> str:
        """Compose a concise llm.txt from crawled pages."""
        if not pages:
            return ""
        
        # Sort pages by importance (depth, content length, etc.)
        sorted_pages = self._prioritize_pages(pages)
        
        # Build content within size limit
        content_parts = []
        total_size = 0
        max_size_bytes = self.max_kb * 1024
        
        # Add header
        header = self._generate_header(pages)
        content_parts.append(header)
        total_size += len(header.encode('utf-8'))
        
        # Add page content
        for page in sorted_pages:
            page_content = self._format_page_content(page, is_full_version=False)
            page_size = len(page_content.encode('utf-8'))
            
            if total_size + page_size > max_size_bytes:
                # Try to fit a truncated version
                remaining_bytes = max_size_bytes - total_size
                if remaining_bytes > 1000:  # Only if we have reasonable space left
                    truncated_content = self._truncate_content(page_content, remaining_bytes)
                    content_parts.append(truncated_content)
                break
            
            content_parts.append(page_content)
            total_size += page_size
        
        # Join all content
        full_content = "\n\n".join(content_parts)
        
        # Use Anthropic to summarize if available and content is too large
        if self.client and len(full_content.encode('utf-8')) > max_size_bytes:
            logger.info("Content exceeds size limit, using AI to summarize")
            return await self._ai_summarize(full_content, target_kb=self.max_kb)
        
        return full_content
    
    async def compose_llms_full_txt(self, pages: List[PageContent]) -> str:
        """Compose a full version with all content."""
        if not pages:
            return ""
        
        # Sort pages by importance
        sorted_pages = self._prioritize_pages(pages)
        
        content_parts = []
        
        # Add header
        header = self._generate_header(pages, is_full_version=True)
        content_parts.append(header)
        
        # Add all page content
        for page in sorted_pages:
            page_content = self._format_page_content(page, is_full_version=True)
            content_parts.append(page_content)
        
        return "\n\n".join(content_parts)
    
    def _prioritize_pages(self, pages: List[PageContent]) -> List[PageContent]:
        """Sort pages by importance for inclusion."""
        def page_score(page: PageContent) -> float:
            score = 0.0
            
            # Prefer pages at lower depth (closer to root)
            score += max(0, 10 - page.depth)
            
            # Prefer pages with more content
            content_length = len(page.content)
            score += min(content_length / 1000, 5)  # Cap at 5 points
            
            # Boost pages with documentation-related keywords in title/URL
            doc_keywords = ['doc', 'guide', 'tutorial', 'api', 'reference', 'getting-started', 'quickstart']
            title_lower = page.title.lower()
            url_lower = page.url.lower()
            
            for keyword in doc_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score += 2
            
            # Penalize changelog, news, blog type content
            low_value_keywords = ['changelog', 'news', 'blog', 'archive', 'release-notes']
            for keyword in low_value_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score -= 5
            
            return score
        
        return sorted(pages, key=page_score, reverse=True)
    
    def _generate_header(self, pages: List[PageContent], is_full_version: bool = False) -> str:
        """Generate header for the llm.txt file."""
        if not pages:
            return "# Documentation Summary\n\nNo content available."
        
        # Get site info from first page
        first_page = pages[0]
        site_title = first_page.title or "Documentation"
        
        version_note = " (Full Version)" if is_full_version else ""
        
        header = f"""# {site_title}{version_note}

This is an AI-generated summary of the documentation.

**Source**: {first_page.url}
**Generated**: {len(pages)} pages crawled
**Total Size**: {sum(len(p.content.encode('utf-8')) for p in pages) / 1024:.1f}KB

---
"""
        return header
    
    def _format_page_content(self, page: PageContent, is_full_version: bool = False) -> str:
        """Format a single page's content."""
        # Use title as section header
        title = page.title or f"Page: {page.url}"
        
        content = f"## {title}\n\n"
        
        if is_full_version:
            content += f"**URL**: {page.url}\n"
            content += f"**Depth**: {page.depth}\n\n"
        
        # Use markdown content if available, otherwise plain text
        page_text = page.markdown if page.markdown.strip() else page.content
        
        # Clean up content
        page_text = self._clean_content(page_text)
        
        content += page_text
        
        return content
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove excessive whitespace
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # Join lines and normalize spacing
        cleaned = '\n\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')
        
        return cleaned.strip()
    
    def _truncate_content(self, content: str, max_bytes: int) -> str:
        """Truncate content to fit within byte limit."""
        if len(content.encode('utf-8')) <= max_bytes:
            return content
        
        # Find a good truncation point
        lines = content.split('\n')
        truncated_lines = []
        current_size = 0
        
        for line in lines:
            line_size = len((line + '\n').encode('utf-8'))
            if current_size + line_size > max_bytes - 100:  # Leave some buffer
                break
            truncated_lines.append(line)
            current_size += line_size
        
        truncated = '\n'.join(truncated_lines)
        truncated += "\n\n[... content truncated due to size limits ...]"
        
        return truncated
    
    async def _ai_summarize(self, content: str, target_kb: int) -> str:
        """Use Anthropic Claude to summarize content to target size."""
        if not self.client:
            # Fallback to simple truncation
            max_bytes = target_kb * 1024
            return self._truncate_content(content, max_bytes)
        
        try:
            prompt = f"""
You are a senior technical writer. Condense the provided documentation into a
concise, accurate **Markdown** summary suitable for inclusion in `llm.txt`.

### OUTPUT RULES
- **Length target:** ~{target_kb} KB when saved as UTF-8. Be terse; prefer bullets.
- **Format:** Output *only* Markdown (no preamble/epilogue). Use this structure:

# <Inferred Title of the Doc/Page>
> 1–2 sentence overview stating purpose and when to use it.

## Key Tasks / Quickstart
- Steps to install/set up/use (max 5 bullets).
- Required tools/versions/auth.

## Core API / Commands (if present)
- Main endpoints/commands with the one-line purpose and essential params.
- Keep code to **one short example** (≤10 lines) enclosed in triple backticks.

## Configuration / Options
- Critical flags, env vars, config keys (name → 1-line meaning; defaults if crucial).

## Constraints & Gotchas
- Limits, common errors, performance/security notes, compatibility/version caveats.

## Links or Section Names (if relevant)
- Important sections/topics to seek (no marketing/history).

### PRIORITIZE
- Getting started; authentication; primary API surface; required parameters; error handling;
  version/compat notes; security/performance constraints.

### DE-PRIORITIZE / OMIT IF NEEDED (to meet size)
- Marketing copy, long narratives, screenshots, repeated navigation, legal boilerplate,
  old changelogs/release notes, acknowledgements.

### COMPRESSION TACTICS
- Replace paragraphs with bullet points.
- Collapse lists (“A, B, C”) instead of multi-line items.
- Shorten phrasing; remove redundancies; keep terminology consistent with the source.

### GUARDRails
- **Do not invent** endpoints, options, or behaviors not present in the source.
- Maintain the source language and key terminology.
- If a section doesn’t exist, omit it—don’t add placeholders.

### SOURCE (truncated to ~50k chars)
{content[:50000]}
"""

            
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = message.content[0].text
            logger.info(f"AI summarization completed. Original: {len(content)}chars, Summary: {len(summary)}chars")
            
            return summary
            
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            # Fallback to truncation
            max_bytes = target_kb * 1024
            return self._truncate_content(content, max_bytes)