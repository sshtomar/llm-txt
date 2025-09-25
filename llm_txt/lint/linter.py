"""Linter for validating llm.txt files."""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp


class LLMTxtLinter:
    """Validate llm.txt files against rules and requirements."""

    def __init__(
        self,
        max_kb: int = 100,
        blocked_paths: Optional[List[str]] = None,
        redact_patterns: Optional[List[str]] = None
    ):
        self.max_kb = max_kb
        self.blocked_paths = blocked_paths or []
        self.redact_patterns = redact_patterns or []

    async def lint(self, file_path: Path) -> Dict:
        """
        Lint an llm.txt file for compliance with rules.

        Returns:
            Dictionary with lint results
        """
        results = {
            'valid': True,
            'size_kb': 0,
            'oversize': False,
            'blocked_content': False,
            'secrets_found': False,
            'broken_links': False,
            'warnings': [],
            'errors': [],
            'link_check_results': {}
        }

        if not file_path.exists():
            results['valid'] = False
            results['errors'].append(f"File not found: {file_path}")
            return results

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Failed to read file: {e}")
            return results

        # Check file size
        size_bytes = len(content.encode('utf-8'))
        results['size_kb'] = size_bytes / 1024

        if results['size_kb'] > self.max_kb:
            results['oversize'] = True
            results['valid'] = False
            results['errors'].append(
                f"File exceeds size limit: {results['size_kb']:.1f} KB > {self.max_kb} KB"
            )

        # Check for blocked paths
        if self._check_blocked_paths(content):
            results['blocked_content'] = True
            results['valid'] = False
            results['errors'].append("Blocked paths detected in content")

        # Check for secrets
        secrets_found = self._check_secrets(content)
        if secrets_found:
            results['secrets_found'] = True
            results['valid'] = False
            results['errors'].append(f"Potential secrets detected: {', '.join(secrets_found)}")

        # Check content structure
        structure_warnings = self._check_structure(content)
        results['warnings'].extend(structure_warnings)

        # Check for broken links
        links = self._extract_links(content)
        if links:
            link_results = await self._check_links(links)
            results['link_check_results'] = link_results

            broken = [url for url, status in link_results.items() if status >= 400 or status == 0]
            if broken:
                results['broken_links'] = True
                results['warnings'].append(f"Broken links detected: {len(broken)}")

        # Check encoding
        if not self._check_encoding(content):
            results['warnings'].append("Non-UTF-8 characters detected")

        return results

    def _check_blocked_paths(self, content: str) -> bool:
        """Check if content contains blocked paths."""
        for blocked_path in self.blocked_paths:
            if blocked_path in content:
                return True
        return False

    def _check_secrets(self, content: str) -> List[str]:
        """Check for potential secrets in content."""
        found_secrets = []

        # Default secret patterns if none provided
        default_patterns = [
            r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?[A-Za-z0-9+/=]{20,}',
            r'(secret|token|password)["\']?\s*[:=]\s*["\']?[A-Za-z0-9+/=]{20,}',
            r'Bearer\s+[A-Za-z0-9+/=]{20,}',
            r'(aws_access_key_id|aws_secret_access_key)\s*=\s*[A-Za-z0-9+/=]{20,}',
            r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'
        ]

        patterns = self.redact_patterns if self.redact_patterns else default_patterns

        for pattern in patterns:
            try:
                if re.search(pattern, content, re.IGNORECASE):
                    found_secrets.append(pattern[:20] + '...')
            except re.error:
                pass

        return found_secrets

    def _check_structure(self, content: str) -> List[str]:
        """Check content structure and completeness."""
        warnings = []

        # Check for required sections
        required_sections = [
            'quickstart|getting.?started|introduction',
            'installation|setup',
            'configuration|config|options',
            'api|reference|commands',
            'error|troubleshoot|debug'
        ]

        content_lower = content.lower()
        for section_pattern in required_sections:
            if not re.search(section_pattern, content_lower):
                section_name = section_pattern.split('|')[0]
                warnings.append(f"Missing recommended section: {section_name}")

        # Check for proper heading structure
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if not headings:
            warnings.append("No headings found in content")
        else:
            # Check heading hierarchy
            prev_level = 0
            for heading_marks, heading_text in headings:
                level = len(heading_marks)
                if prev_level > 0 and level > prev_level + 1:
                    warnings.append(f"Heading level skip: '{heading_text[:30]}...'")
                prev_level = level

        # Check for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if len(code_blocks) > 20:
            warnings.append(f"Excessive code blocks: {len(code_blocks)} found")

        # Check for empty sections
        sections = re.split(r'^#{1,6}\s+', content, flags=re.MULTILINE)[1:]
        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) <= 2:  # Just heading and maybe one line
                warnings.append("Empty or near-empty section detected")
                break

        return warnings

    def _extract_links(self, content: str) -> List[str]:
        """Extract HTTP(S) links from content."""
        # Match markdown links and plain URLs
        markdown_links = re.findall(r'\[.*?\]\((https?://[^)]+)\)', content)
        plain_links = re.findall(r'(?<!\])\bhttps?://[^\s<>"\[\]]+', content)

        all_links = list(set(markdown_links + plain_links))

        # Filter out localhost and example domains
        filtered = []
        for link in all_links:
            if not any(skip in link.lower() for skip in ['localhost', '127.0.0.1', 'example.com', 'example.org']):
                filtered.append(link)

        return filtered[:20]  # Limit to 20 links to avoid excessive checking

    async def _check_links(self, urls: List[str]) -> Dict[str, int]:
        """Check if links are accessible."""
        results = {}

        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                tasks.append(self._check_single_link(session, url))

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for url, response in zip(urls, responses):
                if isinstance(response, Exception):
                    results[url] = 0  # Connection error
                else:
                    results[url] = response

        return results

    async def _check_single_link(self, session: aiohttp.ClientSession, url: str) -> int:
        """Check a single link and return status code."""
        try:
            async with session.head(
                url,
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=True,
                ssl=False
            ) as response:
                return response.status
        except aiohttp.ClientError:
            # Try GET if HEAD fails
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5),
                    allow_redirects=True,
                    ssl=False
                ) as response:
                    return response.status
            except:
                return 0
        except:
            return 0

    def _check_encoding(self, content: str) -> bool:
        """Check if content is valid UTF-8."""
        try:
            content.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False