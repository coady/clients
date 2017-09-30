import collections
import random
import threading
import requests
from requests.compat import json, urljoin
from requests.packages.urllib3.packages.six.moves import map


class Client(requests.Session):
    """A Session which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param headers: additional headers to include in requests
    :param attrs: additional Session attributes
    """
    def __init__(self, url, trailing='', headers=(), **attrs):
        super(Client, self).__init__()
        self.__setstate__(attrs)
        self.headers.update(headers)
        self.trailing = trailing
        self.url = url.rstrip('/') + '/'

    @classmethod
    def clone(cls, other, path=''):
        return cls(urljoin(other.url, path), other.trailing, **other.__getstate__())

    def __truediv__(self, path):
        """Return a cloned client with appended path."""
        return type(self).clone(self, path)
    __div__ = __truediv__

    def request(self, method, path, **kwargs):
        """Send request with relative or absolute path and return response."""
        url = urljoin(self.url, path).rstrip('/') + self.trailing
        return super(Client, self).request(method, url, **kwargs)

    def get(self, path='', **kwargs):
        """GET request with optional path."""
        return super(Client, self).get(path, **kwargs)

    def options(self, path='', **kwargs):
        """OPTIONS request with optional path."""
        return super(Client, self).options(path, **kwargs)

    def head(self, path='', **kwargs):
        """HEAD request with optional path."""
        return super(Client, self).head(path, **kwargs)

    def post(self, path='', json=None, **kwargs):
        """POST request with optional path and json body."""
        return super(Client, self).post(path, json=json, **kwargs)

    def put(self, path='', json=None, **kwargs):
        """PUT request with optional path and json body."""
        return super(Client, self).put(path, json=json, **kwargs)

    def patch(self, path='', json=None, **kwargs):
        """PATCH request with optional path and json body."""
        return super(Client, self).patch(path, json=json, **kwargs)

    def delete(self, path='', **kwargs):
        """DELETE request with optional path."""
        return super(Client, self).delete(path, **kwargs)


class Resource(Client):
    """A `Client`_ which returns json content and has syntactic support for requests."""
    client = property(Client.clone, doc="Upcasted `Client`_.")
    __getitem__ = Client.get
    __setitem__ = Client.put
    __delitem__ = Client.delete

    def __getattr__(self, name):
        """Return a cloned `Resource`_ with appended path."""
        if name in type(self).__attrs__:
            raise AttributeError(name)
        return self / name

    def request(self, method, path, **kwargs):
        """Send request with path and return processed content."""
        response = super(Resource, self).request(method, path, **kwargs)
        response.raise_for_status()
        if response.headers['content-type'].startswith('application/json'):
            return response.json()
        return response.text if response.encoding else response.content

    def iter(self, path='', **kwargs):
        """Iterate lines or chunks from streamed GET request."""
        response = super(Resource, self).request('GET', path, stream=True, **kwargs)
        response.raise_for_status()
        if response.headers['content-type'].startswith('application/json'):
            response.encoding = response.encoding or 'utf8'
            return map(json.loads, response.iter_lines(decode_unicode=True))
        if response.encoding or response.headers['content-type'].startswith('text/'):
            return response.iter_lines(decode_unicode=response.encoding)
        return iter(response)
    __iter__ = iter

    def __contains__(self, path):
        """Return whether endpoint exists according to HEAD request."""
        return super(Resource, self).request('HEAD', path, allow_redirects=False).ok

    def __call__(self, path='', **params):
        """GET request with params."""
        return self.get(path, params=params)

    def update(self, path='', **json):
        """PATCH request with json params."""
        return self.patch(path, json=json)

    def create(self, path='', json=None, **kwargs):
        """POST request and return location."""
        response = super(Resource, self).request('POST', path, json=json, **kwargs)
        response.raise_for_status()
        return response.headers.get('location')

    def download(self, file, path='', **kwargs):
        """Output streamed GET request to file."""
        response = super(Resource, self).request('GET', path, stream=True, **kwargs)
        response.raise_for_status()
        for chunk in response:
            file.write(chunk)
        return file


class Stats(collections.Counter):
    """Thread-safe Counter."""
    def __init__(self):
        self.lock = threading.Lock()

    def update(self, **kwargs):
        with self.lock:
            super(Stats, self).update(kwargs)


class Proxy(Client):
    """An extensible embedded proxy client to multiple hosts.

    The default implementation provides load balancing based on active connections.
    It does not provide error handling or retrying.

    :param urls: base urls for requests
    :param kwargs: same options as `Client`_
    """
    def __init__(self, urls, **kwargs):
        super(Proxy, self).__init__('', **kwargs)
        self.urls = {(url.rstrip('/') + '/'): Stats() for url in urls}

    @classmethod
    def clone(cls, other, path=''):
        urls = (urljoin(url, path) for url in other.urls)
        return cls(urls, trailing=other.trailing, **other.__getstate__())

    def priority(self, url):
        """Return comparable priority for url.

        Minimizes errors, failures (500s), and active connections.
        None may be used to eliminate from consideration.
        """
        stats = self.urls[url]
        return tuple(stats[key] for key in ('errors', 'failures', 'connections'))

    def choice(self, method):
        """Return chosen url according to priority.

        :param method: placeholder for extensions which distinguish read/write requests
        """
        priorities = collections.defaultdict(list)
        for url in self.urls:
            priorities[self.priority(url)].append(url)
        priorities.pop(None, None)
        return random.choice(priorities[min(priorities)])

    def request(self, method, path, **kwargs):
        """Send request with relative or absolute path and return response."""
        url = self.choice(method)
        stats = self.urls[url]
        stats.update(connections=1)
        try:
            response = super(Proxy, self).request(method, urljoin(url, path), **kwargs)
        except IOError:
            stats.update(connections=-1, errors=1)
            raise
        stats.update(connections=-1, failures=int(response.status_code >= 500))
        return response
