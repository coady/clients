import asyncio
import contextlib
from urllib.parse import urljoin
import httpx
from .base import validate, Client, Graph, Proxy, Remote, Resource, TokenAuth


class AsyncClient(httpx.AsyncClient):
    """An asynchronous Client which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param params: default query params
    :param auth: additional authorization support for ``{token_type: access_token}``,
        available per request as well
    :param attrs: additional AsyncClient options
    """

    __truediv__ = Client.__truediv__
    __repr__ = Client.__repr__  # type: ignore
    get = Client.get  # type: ignore
    options = Client.options  # type: ignore
    head = Client.head  # type: ignore
    post = Client.post  # type: ignore
    put = Client.put  # type: ignore
    patch = Client.patch  # type: ignore
    delete = Client.delete  # type: ignore

    def __init__(self, url: str, *, trailing: str = '', auth=None, **attrs):
        attrs['auth'] = TokenAuth(auth) if isinstance(auth, dict) else auth
        super().__init__(base_url=url.rstrip('/') + '/', **attrs)
        self._attrs = attrs
        self.trailing = trailing

    @property
    def url(self):
        return str(self.base_url)

    @classmethod
    def clone(cls, other, path='', **kwargs):
        url = str(other.base_url.join(path))
        kwargs.update(other._attrs)
        return cls(url, trailing=other.trailing, **kwargs)

    def request(self, method, path, auth=None, **kwargs):
        """Send request with relative or absolute path and return response."""
        kwargs['auth'] = TokenAuth(auth) if isinstance(auth, dict) else auth
        url = str(self.base_url.join(path)).rstrip('/') + self.trailing
        return super().request(method, url, **kwargs)

    def run(self, name: str, *args, **kwargs):
        """Synchronously call method and run coroutine."""
        return asyncio.get_event_loop().run_until_complete(getattr(self, name)(*args, **kwargs))


class AsyncResource(AsyncClient):
    """An `AsyncClient`_ which returns json content and has syntactic support for requests."""

    client = property(AsyncClient.clone, doc="upcasted `AsyncClient`_")
    __getattr__ = AsyncClient.__truediv__
    __getitem__ = AsyncClient.get  # type: ignore
    content_type = Resource.content_type
    __call__ = Resource.__call__

    async def request(self, method, path, **kwargs):
        """Send request with path and return processed content."""
        response = await super().request(method, path, **kwargs)
        response.raise_for_status()
        if self.content_type(response) == 'json':
            return response.json()
        return response.text if response.charset_encoding else response.content

    async def updater(self, path='', **kwargs):
        response = await super().request('GET', path, **kwargs)
        response.raise_for_status()
        kwargs['headers'] = dict(kwargs.get('headers', {}), **validate(response))
        yield await self.put(path, (yield response.json()), **kwargs)

    async def updating(self, path: str = '', **kwargs):
        updater = self.updater(path, **kwargs)
        json = await updater.__anext__()
        yield json
        await updater.asend(json)

    if hasattr(contextlib, 'asynccontextmanager'):  # pragma: no branch
        updating = contextlib.asynccontextmanager(updating)
        updating.__doc__ = Resource.updating.__doc__

    async def update(self, path='', callback=None, **json):
        """PATCH request with json params.

        :param callback: optionally update with GET and validated PUT.
            ``callback`` is called on the json result with keyword params, i.e.,
            ``dict`` correctly implements the simple update case.
        """
        if callback is None:
            return await self.patch(path, json)
        updater = self.updater(path)
        return await updater.asend(callback(await updater.__anext__(), **json))

    async def authorize(self, path: str = '', **kwargs) -> dict:
        """Acquire oauth access token and set ``auth``."""
        method = 'GET' if {'json', 'data'}.isdisjoint(kwargs) else 'POST'
        result = await self.request(method, path, **kwargs)
        self._attrs['auth'] = self.auth = TokenAuth({result['token_type']: result['access_token']})
        return result


class AsyncRemote(AsyncClient):
    """An `AsyncClient`_ which defaults to posts with json bodies, i.e., RPC.

    :param url: base url for requests
    :param json: default json body for all calls
    :param kwargs: same options as `AsyncClient`_
    """

    client = AsyncResource.client
    __getattr__ = AsyncResource.__getattr__
    check = staticmethod(Remote.check)

    def __init__(self, url: str, json=(), **kwargs):
        super().__init__(url, **kwargs)
        self.json = dict(json)

    @classmethod
    def clone(cls, other, path=''):
        return AsyncClient.clone.__func__(cls, other, path, json=other.json)

    async def __call__(self, path='', **json):
        """POST request with json body and check result."""
        response = await self.post(path, json=dict(self.json, **json))
        response.raise_for_status()
        return self.check(response.json())


class AsyncGraph(AsyncRemote):
    """An `AsyncRemote`_ client which executes GraphQL queries."""

    Error = httpx.HTTPError
    check = classmethod(Graph.check.__func__)  # type: ignore
    execute = Graph.execute


class AsyncProxy(AsyncClient):
    """An extensible embedded proxy client to multiple hosts.

    The default implementation provides load balancing based on active connections.
    It does not provide error handling or retrying.

    :param urls: base urls for requests
    :param kwargs: same options as `AsyncClient`_
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
