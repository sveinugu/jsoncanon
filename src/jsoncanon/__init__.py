from importlib.metadata import version as _package_version

from .core import canonicalize, is_canonicalized, load_canonicalized, validate_canonicalized

__version__ = _package_version('jsoncanon')
__all__ = ['canonicalize', 'is_canonicalized', 'load_canonicalized', 'validate_canonicalized']
