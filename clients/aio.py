import asyncio
import functools
import operator
import aiohttp
from multidict import MultiDict
from urllib.parse import urljoin
from .base import validate, Client, Graph, Proxy, Remote, Resource


class TokenAuth(aiohttp.BasicAuth):
    __repr__ = encode = functools.partialmethod(' '.join)

    def __new__(cls, auth):
        return tuple.__new__(cls, *auth.items())


class AsyncClient(aiohttp.ClientSession):
    """An asynchronous ClientSession which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param params: default query params
    :param auth: additional authorization support for ``{token_type: access_token}``,
        available per request as well
    :param attrs: additional ClientSession options, e.g., loop
    """
    __truediv__ = Client.__truediv__
    __repr__ = Client.__repr__
    get = Client.get
    options = Client.options
    head = Client.head
    post = Client.post
    put = Client.put
    patch = Client.patch
    delete = Client.delete
    headers = property(operator.attrgetter('_default_headers'), doc="default headers")
    auth = property(operator.attrgetter('_default_auth'), doc="default auth")

    def __init__(self, url, *, trailing='', params=(), auth=None, **attrs):
        if {'connector', 'loop'}.isdisjoint(attrs):
            attrs['loop'] = asyncio.get_event_loop()
        attrs['auth'] = TokenAuth(auth) if isinstance(auth, dict) else auth
        super().__init__(**attrs)
        self._attrs = attrs
        self.params = MultiDict(params)
        self.trailing = trailing
        self.url = url.rstrip('/') + '/'

    def __del__(self):  # avoids warning and race condition in parent
        if self._connector_owner:  # pragma: no branch
            self._connector.close()

    @classmethod
    def clone(cls, other, path='', **kwargs):
        url = urljoin(other.url, path)
        kwargs.update(other._attrs)
        return cls(url, trailing=other.trailing, params=other.params, **kwargs)

    def request(self, method, path, params=(), auth=None, **kwargs):
        kwargs['auth'] = TokenAuth(auth) if isinstance(auth, dict) else auth
        params = MultiDict(params)
        params.extend(self.params)
        url = urljoin(self.url, path).rstrip('/') + self.trailing
        return super().request(method, url, params=params, **kwargs)
    request.__doc__ = Client.request.__doc__

    def run(self, name, *args, **kwargs):
        """Synchronously call method and run coroutine."""
        return self.loop.run_until_complete(getattr(self, name)(*args, **kwargs))


class AsyncResource(AsyncClient):
    """An `AsyncClient`_ which returns json content and has syntactic support for requests."""
    client = property(AsyncClient.clone, doc="upcasted `AsyncClient`_")
    __getattr__ = AsyncClient.__truediv__
    __getitem__ = AsyncClient.get
    content_type = Resource.content_type
    __call__ = Resource.__call__

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self._raise_for_status = True

    async def request(self, method, path, **kwargs):
        response = await super().request(method, path, **kwargs)
        content_type = self.content_type(response)
        if content_type == 'json':
            return await response.json(content_type='')
        return await getattr(response, content_type or 'read')()
    request.__doc__ = Resource.request.__doc__

    async def update(self, path='', callback=None, **json):
        if callback is None:
            return await self.request('PATCH', path, json=json)
        response = await super().request('GET', path)
        json = callback(await response.json(content_type=''), **json)
        return await self.request('PUT', path, json=json, headers=validate(response))
    update.__doc__ = Resource.update.__doc__

    async def authorize(self, path='', **kwargs):
        method = 'GET' if {'json', 'data'}.isdisjoint(kwargs) else 'POST'
        result = await self.request(method, path, **kwargs)
        self._default_auth = TokenAuth({result['token_type']: result['access_token']})
        return result
    authorize.__doc__ = Resource.authorize.__doc__


class AsyncRemote(AsyncClient):
    """An `AsyncClient`_ which defaults to posts with json bodies, i.e., RPC.

    :param url: base url for requests
    :param json: default json body for all calls
    :param kwargs: same options as `AsyncClient`_
    """
    client = AsyncResource.client
    __getattr__ = AsyncResource.__getattr__
    check = staticmethod(Remote.check)

    def __init__(self, url, json=(), **kwargs):
        super().__init__(url, **kwargs)
        self._raise_for_status = True
        self.json = dict(json)

    @classmethod
    def clone(cls, other, path=''):
        return AsyncClient.clone.__func__(cls, other, path, json=other.json)

    async def __call__(self, path='', **json):
        """POST request with json body and check result."""
        response = await self.post(path, json=dict(self.json, **json))
        return self.check(await response.json(content_type=''))


class AsyncGraph(AsyncRemote):
    """An `AsyncRemote`_ client which executes GraphQL queries."""
    Error = aiohttp.ClientPayloadError
    check = classmethod(Graph.check.__func__)
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

    def __init__(self, *urls, **kwargs):
        super().__init__('', **kwargs)
        self.urls = {(url.rstrip('/') + '/'): self.Stats() for url in urls}

    @classmethod
    def clone(cls, other, path=''):
        urls = (urljoin(url, path) for url in other.urls)
        return cls(*urls, trailing=other.trailing, params=other.params, **other._attrs)

    async def request(self, method, path, **kwargs):
        url = self.choice(method)
        with self.urls[url] as stats:
            response = await super().request(method, urljoin(url, path), **kwargs)
        stats.add(failures=int(response.status >= 500))
        return response
    request.__doc__ = Proxy.request.__doc__
