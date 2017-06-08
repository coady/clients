import asyncio
import aiohttp
from urllib.parse import urljoin
from .syncs import Client


class AsyncClient(aiohttp.ClientSession):
    """An asynchronous ClientSession which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param loop: asyncio event loop
    :param attrs: additional ClientSession options, e.g., loop
    """
    __del__ = aiohttp.ClientSession.close
    __truediv__ = Client.__truediv__

    def __init__(self, url, trailing='', **attrs):
        if {'connector', 'loop'}.isdisjoint(attrs):
            attrs['loop'] = asyncio.get_event_loop()
        super().__init__(**attrs)
        self._attrs = attrs
        self.trailing = trailing
        self.url = url.rstrip('/') + '/'

    @classmethod
    def clone(cls, other, path=''):
        return cls(urljoin(other.url, path), other.trailing, **other._attrs)

    def _request(self, method, path, **kwargs):
        """Send request with relative or absolute path and return response."""
        url = urljoin(self.url, path).rstrip('/') + self.trailing
        return super()._request(method, url, **kwargs)

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
