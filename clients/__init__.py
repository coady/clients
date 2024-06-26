from .base import Client, Graph, Proxy, Remote, Resource  # noqa
from .aio import AsyncClient, AsyncGraph, AsyncProxy, AsyncRemote, AsyncResource  # noqa


def singleton(*args, **kwargs):
    """Return a decorator for singleton class instances."""
    return lambda cls: cls(*args, **kwargs)
