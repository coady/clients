from .syncs import Client, Resource  # noqa
try:
    from .asyncs import AsyncClient, AsyncResource  # noqa
except (SyntaxError, ImportError):  # pragma: no cover
    pass

__version__ = '0.4'


def singleton(*args, **kwargs):
    """Return a decorator for singleton class instances."""
    return lambda cls: cls(*args, **kwargs)
