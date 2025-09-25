"""Framework detection for documentation repositories."""

import json
from pathlib import Path
from typing import Optional


class FrameworkDetector:
    """Detect documentation framework used in a repository."""

    def detect(self, repo_path: Path) -> Optional[str]:
        """
        Detect the documentation framework used in the repository.

        Returns:
            Framework name ('docusaurus', 'mkdocs', 'sphinx', 'starlight') or None
        """
        # Check for Docusaurus
        if self._is_docusaurus(repo_path):
            return 'docusaurus'

        # Check for MkDocs
        if self._is_mkdocs(repo_path):
            return 'mkdocs'

        # Check for Sphinx
        if self._is_sphinx(repo_path):
            return 'sphinx'

        # Check for Astro Starlight
        if self._is_starlight(repo_path):
            return 'starlight'

        return None

    def _is_docusaurus(self, repo_path: Path) -> bool:
        """Check if the repository uses Docusaurus."""
        # Check for docusaurus.config.js/ts
        config_files = [
            'docusaurus.config.js',
            'docusaurus.config.ts',
            'docusaurus.config.mjs'
        ]

        for config_file in config_files:
            if (repo_path / config_file).exists():
                return True

        # Check for sidebars.js/ts
        sidebar_files = ['sidebars.js', 'sidebars.ts', 'sidebars.json']
        for sidebar_file in sidebar_files:
            if (repo_path / sidebar_file).exists():
                return True

        # Check package.json for @docusaurus/core
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})

                    if '@docusaurus/core' in deps or '@docusaurus/core' in dev_deps:
                        return True
            except (json.JSONDecodeError, KeyError):
                pass

        return False

    def _is_mkdocs(self, repo_path: Path) -> bool:
        """Check if the repository uses MkDocs."""
        # Check for mkdocs.yml
        config_files = ['mkdocs.yml', 'mkdocs.yaml']

        for config_file in config_files:
            if (repo_path / config_file).exists():
                return True

        # Check for requirements.txt with mkdocs
        requirements = repo_path / 'requirements.txt'
        if requirements.exists():
            try:
                content = requirements.read_text()
                if 'mkdocs' in content.lower():
                    return True
            except Exception:
                pass

        # Check pyproject.toml
        pyproject = repo_path / 'pyproject.toml'
        if pyproject.exists():
            try:
                content = pyproject.read_text()
                if 'mkdocs' in content.lower():
                    return True
            except Exception:
                pass

        return False

    def _is_sphinx(self, repo_path: Path) -> bool:
        """Check if the repository uses Sphinx."""
        # Check for conf.py in docs/source or docs/
        config_paths = [
            repo_path / 'docs' / 'conf.py',
            repo_path / 'docs' / 'source' / 'conf.py',
            repo_path / 'source' / 'conf.py',
            repo_path / 'doc' / 'conf.py'
        ]

        for config_path in config_paths:
            if config_path.exists():
                # Verify it's actually Sphinx conf.py
                try:
                    content = config_path.read_text()
                    if 'sphinx' in content.lower() or 'extensions' in content:
                        return True
                except Exception:
                    pass

        # Check for Makefile with sphinx-build
        makefile = repo_path / 'Makefile'
        if makefile.exists():
            try:
                content = makefile.read_text()
                if 'sphinx-build' in content:
                    return True
            except Exception:
                pass

        return False

    def _is_starlight(self, repo_path: Path) -> bool:
        """Check if the repository uses Astro Starlight."""
        # Check for astro.config.mjs/ts with starlight
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
                    if '@astrojs/starlight' in content:
                        return True
                except Exception:
                    pass

        # Check package.json for @astrojs/starlight
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})

                    if '@astrojs/starlight' in deps or '@astrojs/starlight' in dev_deps:
                        return True
            except (json.JSONDecodeError, KeyError):
                pass

        return False