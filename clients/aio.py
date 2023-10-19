from __future__ import annotations
import asyncio
import contextlib
from typing import Callable, Mapping
from urllib.parse import urljoin
import httpx
from .base import validate, BaseClient, Graph, Proxy, Remote, Resource


class AsyncClient(BaseClient, httpx.AsyncClient):  # type: ignore
    def run(self, name: str, *args, **kwargs):
        """Synchronously call method and run coroutine."""
        return asyncio.new_event_loop().run_until_complete(getattr(self, name)(*args, **kwargs))


class AsyncResource(AsyncClient):
    """An `AsyncClient` which returns json content and has syntactic support for requests."""

    client = property(AsyncClient.clone, doc="upcasted `AsyncClient`")
    __getattr__ = AsyncClient.__truediv__
    __getitem__ = AsyncClient.get
    content_type = Resource.content_type
    __call__ = Resource.__call__

    async def request(self, method, path, **kwargs):
        """Send request with path and return processed content."""
        response = (await super().request(method, path, **kwargs)).raise_for_status()
        if self.content_type(response) == 'json':
            return response.json()
        return response.text if response.encoding else response.content

    async def updater(self, path='', **kwargs):
        response = (await super().request('GET', path, **kwargs)).raise_for_status()
        kwargs['headers'] = dict(kwargs.get('headers', {}), **validate(response))
        yield await self.put(path, (yield response.json()), **kwargs)

    @contextlib.asynccontextmanager
    async def updating(self, path: str = '', **kwargs):
        """Context manager to GET and conditionally PUT json data."""
        updater = self.updater(path, **kwargs)
        json = await updater.__anext__()
        yield json
        await updater.asend(json)

    async def update(self, path: str = '', callback: Callable | None = None, **json):
        """PATCH request with json params.

        Args:
            callback: optionally update with GET and validated PUT.
                `callback` is called on the json result with keyword params, i.e.,
                `dict` correctly implements the simple update case.
        """
        if callback is None:
            return await self.patch(path, json)
        updater = self.updater(path)
        return await updater.asend(callback(await updater.__anext__(), **json))

    async def authorize(self, path: str = '', **kwargs) -> dict:
        """Acquire oauth access token and set `Authorization` header."""
        method = 'GET' if {'json', 'data'}.isdisjoint(kwargs) else 'POST'
        result = await self.request(method, path, **kwargs)
        self.headers['authorization'] = f"{result['token_type']} {result['access_token']}"
        self._attrs['headers'] = self.headers
        return result


class AsyncRemote(AsyncClient):
    """An `AsyncClient` which defaults to posts with json bodies, i.e., RPC.

    Args:
        url: base url for requests
        json: default json body for all calls
        **kwargs: same options as `AsyncClient`
    """

    client = AsyncResource.client
    __getattr__ = AsyncResource.__getattr__
    check = staticmethod(Remote.check)

    def __init__(self, url: str, json: Mapping = {}, **kwargs):
        super().__init__(url, **kwargs)
        self.json = dict(json)

    @classmethod
    def clone(cls, other, path=''):
        return AsyncClient.clone.__func__(cls, other, path, json=other.json)

    async def __call__(self, path='', **json):
        """POST request with json body and check result."""
        response = (await self.post(path, json=dict(self.json, **json))).raise_for_status()
        return self.check(response.json())


class AsyncGraph(AsyncRemote):
    """An `AsyncRemote` client which executes GraphQL queries."""

    Error = httpx.HTTPError
    execute = Graph.execute
    check = classmethod(Graph.check.__func__)  # type: ignore


class AsyncProxy(AsyncClient):
    """An extensible embedded proxy client to multiple hosts.

    The default implementation provides load balancing based on active connections.
    It does not provide error handling or retrying.

    Args:
        *urls: base urls for requests
        **kwargs: same options as `AsyncClient`
    """

    Stats = Proxy.Stats
    priority = Proxy.priority
    choice = Proxy.choice

    def __init__(self, *urls: str, **kwargs):
        super().__init__('https://proxies', **kwargs)
        self.urls = {(url.rstrip('/') + '/'): self.Stats() for url in urls}

    @classmethod
    def clone(cls, other, path=''):
        urls = (urljoin(url, path) for url in other.urls)
        return cls(*urls, trailing=other.trailing, **other._attrs)

    async def request(self, method, path, **kwargs):
        """Send request with relative or absolute path and return response."""
        url = self.choice(method)
        with self.urls[url] as stats:
            response = await super().request(method, urljoin(url, path), **kwargs)
        stats.add(failures=int(response.status_code >= 500))
        return response
