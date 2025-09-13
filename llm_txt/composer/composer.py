"""Composer for generating LLM-friendly text summaries."""

import os
import logging
import re
import hashlib
from typing import List, Optional, Set
import cohere
from dotenv import load_dotenv
from ..crawler.models import PageContent

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMTxtComposer:
    """Composes llm.txt content from crawled pages using Cohere."""
    
    def __init__(self, api_key: Optional[str] = None, max_kb: int = 500) -> None:
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self.max_kb = max_kb
        self.client = None
        
        if self.api_key:
            self.client = cohere.ClientV2(api_key=self.api_key)
        else:
            logger.warning("No Cohere API key provided. Composer will use basic text processing.")
    
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
        
        # Post-process the content
        full_content = self._post_process_content(full_content)
        
        # Use Cohere to summarize if available and content is too large
        if self.client and len(full_content.encode('utf-8')) > max_size_bytes:
            logger.info("Content exceeds size limit, using AI to summarize")
            summarized = await self._ai_summarize(full_content, target_kb=self.max_kb)
            # Post-process the AI output too
            return self._post_process_content(summarized)
        
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
        """Sort pages by importance for inclusion - HuggingFace style."""
        def page_score(page: PageContent) -> float:
            score = 0.0
            
            title_lower = page.title.lower() if page.title else ""
            url_lower = page.url.lower()
            content_lower = page.content[:1000].lower()  # Check first 1000 chars
            
            # HIGHEST PRIORITY: Installation and setup (like HF)
            install_keywords = ['install', 'installation', 'setup', 'getting-started', 
                              'quickstart', 'quick-start', 'requirements', 'dependencies']
            for keyword in install_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score += 25  # Highest boost
                elif keyword in content_lower:
                    score += 15
            
            # HIGH PRIORITY: Core API and usage
            api_keywords = ['api', 'reference', 'methods', 'functions', 'classes',
                           'endpoints', 'parameters', 'arguments', 'options']
            for keyword in api_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score += 20
            
            # HIGH PRIORITY: Examples and tutorials
            example_keywords = ['example', 'tutorial', 'guide', 'how-to', 'usage',
                              'sample', 'demo', 'cookbook', 'recipe']
            for keyword in example_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score += 18
            
            # MEDIUM PRIORITY: Configuration and advanced topics
            config_keywords = ['configuration', 'config', 'settings', 'options',
                             'customize', 'advanced', 'optimization']
            for keyword in config_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score += 10
            
            # BOOST: Code-heavy pages
            code_indicators = ['```', '<code>', 'import ', 'from ', 'def ', 'class ']
            code_count = sum(1 for indicator in code_indicators if indicator in page.content)
            score += min(code_count * 2, 10)  # Cap at 10 points
            
            # PENALTY: Non-technical content
            noise_keywords = [
                'changelog', 'release', 'announcement', 'blog', 'news',
                'about', 'careers', 'team', 'company', 'press',
                'terms', 'privacy', 'cookie', 'legal', 'disclaimer',
                'pricing', 'plans', 'enterprise', 'contact', 'support'
            ]
            for keyword in noise_keywords:
                if keyword in title_lower or keyword in url_lower:
                    score -= 30  # Heavy penalty
            
            # PENALTY: Date patterns (changelogs/blogs)
            if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}|changelog|release-notes', url_lower):
                score -= 25
            
            # Depth scoring: prefer shallow pages for main concepts
            if page.depth <= 2:
                score += 5
            elif page.depth > 4:
                score -= 5
            
            # Content length scoring
            content_length = len(page.content)
            if 1000 < content_length < 30000:  # Optimal range
                score += 5
            elif content_length > 100000:  # Too long, probably aggregated
                score -= 10
            
            return score
        
        # Deduplicate pages before sorting
        unique_pages = self._deduplicate_pages(pages)
        return sorted(unique_pages, key=page_score, reverse=True)
    
    def _generate_header(self, pages: List[PageContent], is_full_version: bool = False) -> str:
        """Generate minimal header for the llm.txt file."""
        if not pages:
            return ""
        
        # For AI-summarized version, let the AI generate the header
        # For full version, add a simple comment
        if is_full_version:
            return f"# Documentation\n\n"
        else:
            return ""  # Let AI generate appropriate title
    
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
        """Clean and normalize content - enhanced version."""
        # Step 1: Remove HTML tags and custom tags
        html_patterns = [
            r'<[^>]+>',  # HTML tags
            r'<Tip[^>]*>.*?</Tip>',  # Custom tip tags
            r'\{\{[^}]+\}\}',  # Template variables
        ]
        for pattern in html_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Step 2: Clean code blocks
        # Fix malformed code blocks with line numbers
        def clean_code_block(match):
            code = match.group(1)
            # Remove line numbers in various formats
            code = re.sub(r'^\d+\|\s*', '', code, flags=re.MULTILINE)
            code = re.sub(r'^\s*---\|---.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^\s*\|\s*', '', code, flags=re.MULTILINE)
            return f'```\n{code.strip()}\n```'
        
        content = re.sub(r'```[\w]*\n([^`]+)```', clean_code_block, content, flags=re.DOTALL)
        
        # Step 3: Remove navigation and UI elements
        noise_patterns = [
            r'GET\s+STARTED.*?(?=\n|$)',
            r'Built\s+with.*?(?=\n|$)',
            r'\[.*?GET\s+STARTED.*?\]\(.*?\)',
            r'\[Built\s+with\].*?(?=\n|$)',
            r'\[.*?\]\(#[^)]*\)',  # Internal anchor links
            r'^\s*\[/.*?\].*$',  # Navigation paths
            r'^\s*\|\s*$',  # Empty table rows
            r'Read\s+more.*?(?=\n|$)',
            r'Learn\s+more.*?(?=\n|$)',
            r'Click\s+here.*?(?=\n|$)',
            r'^\s*→.*$',  # Arrow navigation
            r'^\s*[▶▼►◄].*$',  # UI symbols
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Step 4: Clean up whitespace and formatting
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.rstrip()  # Keep left indentation for code
            
            # Skip multiple consecutive empty lines
            if not line:
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        content = '\n'.join(cleaned_lines)
        
        # Step 5: Fix markdown formatting issues
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 newlines
        content = re.sub(r'^#{7,}', '######', content, flags=re.MULTILINE)  # Max 6 header levels
        
        return content.strip()
    
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
        """Use Cohere to summarize content to target size."""
        if not self.client:
            # Fallback to simple truncation
            max_bytes = target_kb * 1024
            return self._truncate_content(content, max_bytes)
        
        try:
            system_prompt = f"""<role>
You are a senior technical documentation specialist with expertise in creating LLM-optimized reference materials. You excel at analyzing complex documentation and synthesizing it into clean, structured formats.
</role>

<task>
Transform the provided documentation into a comprehensive technical reference optimized for LLMs and developers.
</task>

<requirements>
1. Extract installation instructions, setup procedures, and dependencies
2. Identify core APIs, methods, and configuration options
3. Preserve clean, runnable code examples without artifacts
4. Organize content by practical importance (setup → basic usage → advanced)
5. Remove all non-technical content (marketing, changelogs, navigation)
6. Maintain technical accuracy while improving clarity
7. Target approximately {target_kb} KB of content
</requirements>

<output_format>
# [Project/Library Name]

## Installation

### Prerequisites
- Required dependencies and system requirements
- Version compatibility information

### Install with pip
```bash
pip install [package-name]
```

### Install from source
```bash
git clone [repository]
cd [directory]
pip install -e .
```

## Quick Start

Brief description of what this library does and its primary use case.

```python
# Minimal working example
from library import MainClass
client = MainClass(api_key="...")
result = client.method()
```

## Core API

### [Primary Class/Function]

**Purpose**: One-line description
**Parameters**:
- `param_name` (type): Description
- `optional_param` (type, optional): Description

**Example**:
```python
# Clean, complete example
result = function(param="value")
```

## Configuration

### Environment Variables
- `ENV_VAR_NAME`: Description (default: value)

### Configuration Options
```python
config = {{
    "option": "value",
    "timeout": 30
}}
```

## Common Patterns

### [Use Case 1]
```python
# Complete example for common use case
```

### [Use Case 2]
```python
# Another practical example
```

## Advanced Usage

### Performance Optimization
- Technique 1: Description
- Technique 2: Description

### Error Handling
```python
try:
    result = client.method()
except SpecificError as e:
    # Handle error
```

## Troubleshooting

### Common Issues
- **Issue**: Solution
- **Error Message**: What it means and how to fix

## API Reference

### Methods
- `method_name(params)`: Description
- `another_method(params)`: Description

### Models Available
- `model-name`: Capabilities and use cases
</output_format>

<content_rules>
- REMOVE: All changelog entries, release notes, announcements, dates
- REMOVE: Marketing language, company information, promotional content
- REMOVE: Navigation elements, UI components, buttons, links to social media
- REMOVE: Malformed code with line numbers (1|, 2|, ---|---)
- CLEAN: Code blocks must be properly formatted with language tags
- PRESERVE: Technical accuracy, parameter names, API signatures
- FOCUS: Practical implementation details developers need
- STRUCTURE: Maintain consistent header hierarchy without skipping levels
</content_rules>

<quality_checks>
Before finalizing:
1. Verify all code examples are complete and runnable
2. Ensure installation instructions are clear and complete
3. Check that API documentation includes all essential parameters
4. Confirm no marketing or changelog content remains
5. Validate markdown formatting is clean and consistent
</quality_checks>"""
            
            user_message = f"""<documents>
<document>
<source>Technical Documentation</source>
<content>
{content[:50000]}
</content>
</document>
</documents>

<instruction>
Analyze the documentation above and create a structured technical reference following the specified format. Focus on extracting practical, actionable information that developers need.
</instruction>"""
            
            response = self.client.chat(
                model="command-r-plus-08-2024",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,
                seed=42,  # For deterministic output
                max_tokens=4000
            )
            
            summary = response.message.content[0].text
            logger.info(f"AI summarization completed. Original: {len(content)}chars, Summary: {len(summary)}chars")
            
            return summary
            
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            # Fallback to truncation
            max_bytes = target_kb * 1024
            return self._truncate_content(content, max_bytes)
    
    def _deduplicate_pages(self, pages: List[PageContent]) -> List[PageContent]:
        """Remove duplicate content based on content hash."""
        seen_hashes: Set[str] = set()
        unique_pages = []
        
        for page in pages:
            # Create hash of normalized content
            content_hash = hashlib.md5(
                self._clean_content(page.content).encode('utf-8')
            ).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_pages.append(page)
            else:
                logger.debug(f"Skipping duplicate content from: {page.url}")
        
        return unique_pages
    
    def _post_process_content(self, content: str) -> str:
        """Final post-processing to ensure clean output."""
        # Remove any remaining artifacts
        content = re.sub(r'\[\[.*?\]\]', '', content)  # Remove wiki-style links
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)  # Remove HTML comments
        
        # Ensure consistent header hierarchy
        lines = content.split('\n')
        processed_lines = []
        header_stack = []
        
        header_re = re.compile(r'^(#+)\s*(.*)$')
        for line in lines:
            # Track and fix header hierarchy robustly
            if line.startswith('#'):
                m = header_re.match(line)
                if m:
                    level = len(m.group(1))
                    text = m.group(2) or ""
                    # Ensure we don't skip header levels
                    if header_stack and level > header_stack[-1] + 1:
                        level = header_stack[-1] + 1
                    # Rebuild header safely even if there was no space/text
                    line = ('#' * level) + ((' ' + text) if text else '')

                    # Update header stack
                    while header_stack and header_stack[-1] >= level:
                        header_stack.pop()
                    header_stack.append(level)
                # If regex didn't match, fall through and keep line as-is

            processed_lines.append(line)
        
        content = '\n'.join(processed_lines)
        
        # Final cleanup
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)  # Remove whitespace-only lines
        
        return content.strip()

    # Quality validation added to support JobManager usage
    def _validate_output_quality(self, content: str):
        """Lightweight sanity checks for composed content.

        Returns a tuple (is_valid, issues).
        Keeps checks conservative to avoid false negatives.
        """
        issues: list[str] = []
        text = content or ""

        if not text.strip():
            issues.append("Empty content")

        # Check unbalanced fenced code blocks (```)
        fences = text.count("```")
        if fences % 2 == 1:
            issues.append("Unclosed fenced code block")

        # Check for excessive size (very rough guard, independent of budgeting)
        if len(text) > (self.max_kb * 1024 * 2):
            issues.append("Output exceeds 2x configured max_kb")

        # Basic header structure heuristic (optional)
        # Not strictly required; skip strict enforcement to keep valid
        # developer docs that start without a title.

        return (len(issues) == 0, issues)
