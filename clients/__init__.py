from .base import Client, Graph, Proxy, Remote, Resource  # noqa

try:
    from .aio import AsyncClient, AsyncGraph, AsyncProxy, AsyncRemote, AsyncResource  # noqa
except SyntaxError:  # pragma: no cover
    pass

__version__ = '1.1'


def singleton(*args, **kwargs):
    """Return a decorator for singleton class instances."""
    return lambda cls: cls(*args, **kwargs)
