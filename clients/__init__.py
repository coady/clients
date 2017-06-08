from .syncs import Client, Resource  # noqa
try:
    from .asyncs import AsyncClient  # noqa
except ImportError:  # pragma: no cover
    pass

__version__ = '0.3'


def singleton(*args, **kwargs):
    """Return a decorator for singleton class instances."""
    return lambda cls: cls(*args, **kwargs)
