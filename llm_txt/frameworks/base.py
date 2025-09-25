"""Base class for framework adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional


class FrameworkAdapter(ABC):
    """Abstract base class for documentation framework adapters."""

    @abstractmethod
    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """
        Extract navigation structure from the framework configuration.

        Returns:
            Navigation structure as a dictionary or None
        """
        pass

    @abstractmethod
    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """
        Get the paths where documentation files are located.

        Returns:
            List of paths to search for documentation files
        """
        pass

    @abstractmethod
    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """
        Get the priority of a page based on its position in navigation.

        Lower numbers = higher priority.

        Returns:
            Priority score (0-100)
        """
        pass

    def extract_front_matter(self, content: str) -> Dict:
        """
        Extract front matter from a markdown file.

        Returns:
            Dictionary of front matter fields
        """
        import yaml
        import re

        # Match YAML front matter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}

        return {}

    def get_title_from_file(self, file_path: Path) -> Optional[str]:
        """
        Extract title from a documentation file.

        Checks front matter first, then falls back to first H1.
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Check front matter
            front_matter = self.extract_front_matter(content)
            if 'title' in front_matter:
                return front_matter['title']

            # Look for first H1
            import re
            h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if h1_match:
                return h1_match.group(1).strip()

            # Use filename as fallback
            return file_path.stem.replace('-', ' ').replace('_', ' ').title()

        except Exception:
            return None