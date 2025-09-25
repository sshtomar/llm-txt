"""Framework-specific adapters for various documentation systems."""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from .base import FrameworkAdapter


class DocusaurusAdapter(FrameworkAdapter):
    """Adapter for Docusaurus documentation framework."""

    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """Extract navigation from sidebars.js/json."""
        sidebar_files = [
            'sidebars.js',
            'sidebars.ts',
            'sidebars.json'
        ]

        for sidebar_file in sidebar_files:
            sidebar_path = repo_path / sidebar_file
            if sidebar_path.exists():
                if sidebar_file.endswith('.json'):
                    try:
                        with open(sidebar_path) as f:
                            return json.load(f)
                    except json.JSONDecodeError:
                        pass
                else:
                    # For JS/TS files, try to extract the exported object
                    # This is simplified - real implementation would need proper JS parsing
                    try:
                        content = sidebar_path.read_text()
                        # Look for module.exports or export default
                        import re
                        match = re.search(r'(?:module\.exports|export\s+default)\s*=\s*({[\s\S]+});?', content)
                        if match:
                            # Try to parse as JSON-like structure
                            # Note: This is a simplified approach
                            return {'tutorialSidebar': []}
                    except Exception:
                        pass

        return None

    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """Get documentation paths for Docusaurus."""
        paths = []

        # Standard Docusaurus paths
        standard_paths = [
            repo_path / 'docs',
            repo_path / 'website' / 'docs',
            repo_path / 'src' / 'pages',
            repo_path / 'blog'
        ]

        for path in standard_paths:
            if path.exists() and path.is_dir():
                paths.append(path)

        # Check docusaurus.config for custom paths
        config_files = [
            'docusaurus.config.js',
            'docusaurus.config.ts',
            'docusaurus.config.mjs'
        ]

        for config_file in config_files:
            config_path = repo_path / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text()
                    # Look for docs path configuration
                    import re
                    match = re.search(r"path:\s*['\"](.+?)['\"]", content)
                    if match:
                        custom_path = repo_path / match.group(1)
                        if custom_path.exists() and custom_path not in paths:
                            paths.append(custom_path)
                except Exception:
                    pass

        return paths if paths else [repo_path]

    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """Get page priority based on Docusaurus conventions."""
        filename = file_path.stem.lower()

        # High priority pages
        if filename in ['index', 'intro', 'introduction', 'getting-started', 'quickstart']:
            return 0
        elif filename in ['installation', 'setup', 'configuration', 'config']:
            return 5
        elif filename in ['api', 'reference', 'api-reference']:
            return 10
        elif filename in ['tutorial', 'guide', 'how-to']:
            return 15

        # Check if it's in the sidebar structure
        if nav_structure:
            # Simplified - would need to traverse the structure properly
            return 20

        # Check for number prefixes (01-intro.md, etc.)
        import re
        if re.match(r'^\d+[-_]', filename):
            return 25

        return 50


class MkDocsAdapter(FrameworkAdapter):
    """Adapter for MkDocs documentation framework."""

    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """Extract navigation from mkdocs.yml."""
        config_files = ['mkdocs.yml', 'mkdocs.yaml']

        for config_file in config_files:
            config_path = repo_path / config_file
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        return config.get('nav', config.get('pages'))
                except yaml.YAMLError:
                    pass

        return None

    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """Get documentation paths for MkDocs."""
        # Read from mkdocs.yml
        config_files = ['mkdocs.yml', 'mkdocs.yaml']

        for config_file in config_files:
            config_path = repo_path / config_file
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        docs_dir = config.get('docs_dir', 'docs')
                        path = repo_path / docs_dir
                        if path.exists():
                            return [path]
                except yaml.YAMLError:
                    pass

        # Fallback to default
        default_path = repo_path / 'docs'
        if default_path.exists():
            return [default_path]

        return [repo_path]

    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """Get page priority based on MkDocs navigation."""
        filename = file_path.stem.lower()

        # High priority pages
        if filename in ['index', 'home']:
            return 0
        elif filename in ['getting-started', 'quickstart', 'installation']:
            return 5
        elif filename in ['user-guide', 'guide', 'tutorial']:
            return 10
        elif filename in ['api', 'reference', 'api-reference']:
            return 15
        elif filename in ['configuration', 'config', 'settings']:
            return 20

        # Check position in nav structure
        if nav_structure and isinstance(nav_structure, list):
            # Traverse nav structure to find position
            for idx, item in enumerate(nav_structure):
                if self._find_in_nav(file_path.name, item):
                    return 25 + idx

        return 50

    def _find_in_nav(self, filename: str, nav_item) -> bool:
        """Helper to find a file in navigation structure."""
        if isinstance(nav_item, dict):
            for value in nav_item.values():
                if isinstance(value, str) and filename in value:
                    return True
                elif isinstance(value, list):
                    for item in value:
                        if self._find_in_nav(filename, item):
                            return True
        elif isinstance(nav_item, str) and filename in nav_item:
            return True

        return False


class SphinxAdapter(FrameworkAdapter):
    """Adapter for Sphinx documentation framework."""

    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """Extract navigation from index.rst or toctree directives."""
        # Find index.rst
        index_paths = [
            repo_path / 'docs' / 'source' / 'index.rst',
            repo_path / 'docs' / 'index.rst',
            repo_path / 'source' / 'index.rst',
            repo_path / 'doc' / 'index.rst',
            repo_path / 'index.rst'
        ]

        for index_path in index_paths:
            if index_path.exists():
                try:
                    content = index_path.read_text()
                    # Extract toctree entries
                    import re
                    toctree_pattern = r'.. toctree::[\s\S]*?(?=\n\n|\n.. |\Z)'
                    matches = re.findall(toctree_pattern, content)

                    if matches:
                        # Simplified extraction
                        return {'toctree': matches}
                except Exception:
                    pass

        return None

    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """Get documentation paths for Sphinx."""
        paths = []

        # Common Sphinx paths
        common_paths = [
            repo_path / 'docs' / 'source',
            repo_path / 'docs',
            repo_path / 'source',
            repo_path / 'doc' / 'source',
            repo_path / 'doc'
        ]

        for path in common_paths:
            if path.exists() and path.is_dir():
                # Check if it contains .rst or .md files
                if any(path.glob('*.rst')) or any(path.glob('*.md')):
                    paths.append(path)

        return paths if paths else [repo_path]

    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """Get page priority for Sphinx documentation."""
        filename = file_path.stem.lower()

        # High priority pages
        if filename == 'index':
            return 0
        elif filename in ['quickstart', 'getting_started', 'introduction']:
            return 5
        elif filename in ['installation', 'install', 'setup']:
            return 10
        elif filename in ['tutorial', 'tutorials', 'guide']:
            return 15
        elif filename in ['api', 'reference', 'api_reference']:
            return 20
        elif filename in ['configuration', 'config']:
            return 25

        return 50


class StarlightAdapter(FrameworkAdapter):
    """Adapter for Astro Starlight documentation framework."""

    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """Extract navigation from Astro config."""
        config_files = [
            'astro.config.mjs',
            'astro.config.ts',
            'astro.config.js'
        ]

        for config_file in config_files:
            config_path = repo_path / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text()
                    # Look for sidebar configuration
                    import re
                    sidebar_match = re.search(r'sidebar:\s*\[([\s\S]*?)\]', content)
                    if sidebar_match:
                        # Simplified - would need proper JS parsing
                        return {'sidebar': []}
                except Exception:
                    pass

        return None

    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """Get documentation paths for Starlight."""
        paths = []

        # Standard Starlight content paths
        standard_paths = [
            repo_path / 'src' / 'content' / 'docs',
            repo_path / 'src' / 'content',
            repo_path / 'content' / 'docs',
            repo_path / 'docs'
        ]

        for path in standard_paths:
            if path.exists() and path.is_dir():
                paths.append(path)

        return paths if paths else [repo_path]

    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """Get page priority for Starlight pages."""
        filename = file_path.stem.lower()

        # Check front matter for order
        try:
            content = file_path.read_text(encoding='utf-8')
            front_matter = self.extract_front_matter(content)

            if 'order' in front_matter:
                return int(front_matter['order'])
            elif 'sidebar' in front_matter:
                sidebar = front_matter['sidebar']
                if isinstance(sidebar, dict) and 'order' in sidebar:
                    return int(sidebar['order'])
        except (ValueError, Exception):
            pass

        # High priority pages by name
        if filename in ['index', 'intro', 'introduction']:
            return 0
        elif filename in ['getting-started', 'quickstart']:
            return 5
        elif filename in ['installation', 'setup']:
            return 10
        elif filename in ['configuration', 'config']:
            return 15

        # Check parent directory for grouping
        parent = file_path.parent.name.lower()
        if parent in ['guides', 'tutorials']:
            return 20
        elif parent in ['api', 'reference']:
            return 25

        return 50


class GenericAdapter(FrameworkAdapter):
    """Generic adapter for unrecognized documentation structures."""

    def get_navigation(self, repo_path: Path) -> Optional[Dict]:
        """No specific navigation for generic repos."""
        return None

    def get_docs_paths(self, repo_path: Path) -> List[Path]:
        """Look for common documentation directories."""
        paths = []

        # Common documentation directory names
        common_dirs = [
            'docs', 'doc', 'documentation',
            'wiki', 'guide', 'guides',
            'manual', 'help'
        ]

        for dir_name in common_dirs:
            path = repo_path / dir_name
            if path.exists() and path.is_dir():
                paths.append(path)

        # Also check src directories
        src_docs = [
            repo_path / 'src' / 'docs',
            repo_path / 'source' / 'docs'
        ]

        for path in src_docs:
            if path.exists() and path.is_dir():
                paths.append(path)

        # If no specific docs directory, use repo root
        return paths if paths else [repo_path]

    def get_page_priority(self, file_path: Path, nav_structure: Optional[Dict]) -> int:
        """Basic priority based on filename patterns."""
        filename = file_path.stem.lower()

        # README files are high priority
        if filename == 'readme':
            return 0
        elif filename in ['index', 'home']:
            return 5
        elif 'start' in filename or 'intro' in filename:
            return 10
        elif 'install' in filename or 'setup' in filename:
            return 15
        elif 'guide' in filename or 'tutorial' in filename:
            return 20
        elif 'api' in filename or 'reference' in filename:
            return 25
        elif 'config' in filename:
            return 30
        elif 'faq' in filename or 'troubleshoot' in filename:
            return 35

        # Check for numbered files
        import re
        if re.match(r'^\d+[-_.]', filename):
            # Extract number and use as priority
            num_match = re.match(r'^(\d+)', filename)
            if num_match:
                return min(40 + int(num_match.group(1)), 100)

        return 50