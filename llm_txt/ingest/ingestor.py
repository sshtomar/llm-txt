"""Repository file ingestion and processing."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fnmatch import fnmatch

from ..frameworks.base import FrameworkAdapter


class Page:
    """Represents a documentation page."""

    def __init__(
        self,
        path: Path,
        title: str,
        content: str,
        priority: int = 50,
        metadata: Optional[Dict] = None
    ):
        self.path = path
        self.title = title
        self.content = content
        self.priority = priority
        self.metadata = metadata or {}
        self.url = self._generate_url()

    def _generate_url(self) -> str:
        """Generate a URL-like path for the page."""
        # Convert file path to URL path
        path_str = str(self.path)
        # Remove common prefixes
        for prefix in ['docs/', 'src/content/docs/', 'source/']:
            if prefix in path_str:
                path_str = path_str.split(prefix)[-1]

        # Remove extension and convert to URL
        url = path_str.replace('.md', '').replace('.mdx', '').replace('.rst', '')
        url = url.replace('\\', '/').replace('/index', '')

        # Ensure it starts with /
        if not url.startswith('/'):
            url = '/' + url

        return url

    def __repr__(self) -> str:
        return f"Page(title='{self.title}', url='{self.url}', priority={self.priority})"


class RepoIngestor:
    """Ingest and process documentation files from a repository."""

    def __init__(
        self,
        include_patterns: List[str],
        exclude_patterns: List[str],
        framework_adapter: Optional[FrameworkAdapter] = None
    ):
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.framework_adapter = framework_adapter

    def ingest(self, repo_path: Path) -> List[Page]:
        """
        Ingest documentation files from the repository.

        Returns:
            List of Page objects sorted by priority
        """
        pages = []

        # Get docs paths from framework adapter
        if self.framework_adapter:
            docs_paths = self.framework_adapter.get_docs_paths(repo_path)
            nav_structure = self.framework_adapter.get_navigation(repo_path)
        else:
            docs_paths = [repo_path]
            nav_structure = None

        # Find all matching files
        for docs_path in docs_paths:
            for file_path in self._find_files(docs_path):
                # Check if file should be included
                if not self._should_include(file_path, repo_path):
                    continue

                # Read and process the file
                try:
                    page = self._process_file(file_path, nav_structure, repo_path)
                    if page:
                        pages.append(page)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error processing {file_path}: {e}")

        # Sort by priority (lower = higher priority)
        pages.sort(key=lambda p: (p.priority, p.title))

        return pages

    def _find_files(self, path: Path) -> List[Path]:
        """Recursively find all documentation files."""
        files = []

        if not path.exists():
            return files

        # Supported extensions
        extensions = ['.md', '.mdx', '.rst']

        for ext in extensions:
            files.extend(path.rglob(f'*{ext}'))

        return files

    def _should_include(self, file_path: Path, repo_path: Path) -> bool:
        """Check if a file should be included based on patterns."""
        # Get relative path from repo root
        try:
            rel_path = file_path.relative_to(repo_path)
        except ValueError:
            # File is outside repo, include by default
            rel_path = file_path

        rel_str = str(rel_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch(rel_str, pattern) or fnmatch(f'**/{rel_str}', pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if fnmatch(rel_str, pattern) or fnmatch(f'**/{rel_str}', pattern):
                return True

        # Default to exclude if no include pattern matches
        return False

    def _process_file(
        self,
        file_path: Path,
        nav_structure: Optional[Dict],
        repo_path: Path
    ) -> Optional[Page]:
        """Process a documentation file into a Page object."""
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')

            # Extract metadata and clean content
            metadata, clean_content = self._extract_metadata(content)

            # Get title
            if self.framework_adapter:
                title = self.framework_adapter.get_title_from_file(file_path)
            else:
                title = metadata.get('title') or self._extract_title(clean_content, file_path)

            if not title:
                title = file_path.stem.replace('-', ' ').replace('_', ' ').title()

            # Get priority
            if self.framework_adapter:
                priority = self.framework_adapter.get_page_priority(file_path, nav_structure)
            else:
                priority = self._calculate_priority(file_path, metadata)

            # Clean and normalize content
            clean_content = self._clean_content(clean_content)

            # Create page object
            page = Page(
                path=file_path.relative_to(repo_path),
                title=title,
                content=clean_content,
                priority=priority,
                metadata=metadata
            )

            return page

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")
            return None

    def _extract_metadata(self, content: str) -> Tuple[Dict, str]:
        """Extract front matter metadata and return clean content."""
        import yaml

        # Match YAML front matter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if match:
            try:
                metadata = yaml.safe_load(match.group(1)) or {}
                clean_content = content[match.end():]
                return metadata, clean_content
            except yaml.YAMLError:
                pass

        return {}, content

    def _extract_title(self, content: str, file_path: Path) -> Optional[str]:
        """Extract title from content."""
        # Look for first H1
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Look for first H2 if no H1
        h2_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if h2_match:
            return h2_match.group(1).strip()

        return None

    def _calculate_priority(self, file_path: Path, metadata: Dict) -> int:
        """Calculate priority for a page without framework context."""
        # Check metadata first
        if 'priority' in metadata:
            try:
                return int(metadata['priority'])
            except (ValueError, TypeError):
                pass

        if 'order' in metadata:
            try:
                return int(metadata['order'])
            except (ValueError, TypeError):
                pass

        # Use filename patterns
        filename = file_path.stem.lower()

        priority_map = {
            'readme': 0,
            'index': 5,
            'intro': 10,
            'introduction': 10,
            'getting-started': 15,
            'quickstart': 15,
            'installation': 20,
            'setup': 20,
            'tutorial': 25,
            'guide': 25,
            'api': 30,
            'reference': 30,
            'configuration': 35,
            'config': 35,
            'faq': 40,
            'troubleshooting': 40,
            'changelog': 90,
            'contributing': 95,
            'license': 100
        }

        # Check exact matches
        if filename in priority_map:
            return priority_map[filename]

        # Check partial matches
        for key, priority in priority_map.items():
            if key in filename:
                return priority

        # Check for numbered files
        num_match = re.match(r'^(\d+)[-_.]', filename)
        if num_match:
            return 50 + int(num_match.group(1))

        return 50

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Normalize code blocks
        content = re.sub(r'```(\w+)?\n', r'```\1\n', content)

        # Remove trailing whitespace
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        content = '\n'.join(lines)

        return content.strip()