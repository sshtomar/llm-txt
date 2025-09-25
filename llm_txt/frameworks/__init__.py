"""Framework detection and adapters for documentation repositories."""

from .detector import FrameworkDetector
from .base import FrameworkAdapter
from .adapters import (
    DocusaurusAdapter,
    MkDocsAdapter,
    SphinxAdapter,
    StarlightAdapter,
    GenericAdapter
)

__all__ = [
    'FrameworkDetector',
    'FrameworkAdapter',
    'DocusaurusAdapter',
    'MkDocsAdapter',
    'SphinxAdapter',
    'StarlightAdapter',
    'GenericAdapter',
    'get_framework_adapter'
]


def get_framework_adapter(name: str) -> FrameworkAdapter:
    """Get framework adapter by name."""
    adapters = {
        'docusaurus': DocusaurusAdapter,
        'mkdocs': MkDocsAdapter,
        'sphinx': SphinxAdapter,
        'starlight': StarlightAdapter,
        'generic': GenericAdapter
    }

    adapter_class = adapters.get(name.lower(), GenericAdapter)
    return adapter_class()