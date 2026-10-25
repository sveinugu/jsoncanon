from importlib.metadata import version

from .core import canonicalize, is_canonicalized, load_canonicalized, validate_canonicalized

__version__ = version('jsoncanon')
__all__ = ['canonicalize', 'is_canonicalized', 'load_canonicalized', 'validate_canonicalized']
