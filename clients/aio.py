import asyncio
import aiohttp
from multidict import MultiDict
from urllib.parse import urljoin
from .base import Client, Remote, Resource


class AsyncClient(aiohttp.ClientSession):
    """An asynchronous ClientSession which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param params: default query params
    :param attrs: additional ClientSession options, e.g., loop
    """
    __truediv__ = Client.__truediv__

    def __init__(self, url, *, trailing='', params=(), **attrs):
        if {'connector', 'loop'}.isdisjoint(attrs):
            attrs['loop'] = asyncio.get_event_loop()
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

    def _request(self, method, path, params=(), **kwargs):
        params = MultiDict(params)
        params.extend(self.params)
        url = urljoin(self.url, path).rstrip('/') + self.trailing
        return super()._request(method, url, params=params, **kwargs)

    def get(self, path='', **kwargs):
        """GET request with optional path."""
        return super().get(path, **kwargs)

    def options(self, path='', **kwargs):
        """OPTIONS request with optional path."""
        return super().options(path, **kwargs)

    def head(self, path='', **kwargs):
        """HEAD request with optional path."""
        return super().head(path, **kwargs)

    def post(self, path='', json=None, **kwargs):
        """POST request with optional path and json body."""
        return super().post(path, json=json, **kwargs)

    def put(self, path='', json=None, **kwargs):
        """PUT request with optional path and json body."""
        return super().put(path, json=json, **kwargs)

    def patch(self, path='', json=None, **kwargs):
        """PATCH request with optional path and json body."""
        return super().patch(path, json=json, **kwargs)

    def delete(self, path='', **kwargs):
        """DELETE request with optional path."""
        return super().delete(path, **kwargs)


class AsyncResource(AsyncClient):
    """An `AsyncClient`_ which returns json content and has syntactic support for requests."""
    client = property(AsyncClient.clone, doc="Upcasted `AsyncClient`_.")
    __getattr__ = AsyncClient.__truediv__
    __getitem__ = AsyncClient.get
    __call__ = Resource.__call__
    update = Resource.update

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self._raise_for_status = True

    @asyncio.coroutine
    def _request(self, method, path, **kwargs):
        """Send request with relative or absolute path and return response."""
        response = yield from super()._request(method, path, **kwargs)
        if response.headers['content-type'].startswith('application/json'):
            return (yield from response.json())
        if response.headers['content-type'].startswith('text/'):
            return (yield from response.text())
        return (yield from response.read())


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

    @asyncio.coroutine
    def __call__(self, path='', **json):
        """POST request with json body and check result."""
        response = yield from self.post(path, json=dict(self.json, **json))
        result = yield from response.json()
        return self.check(result)
