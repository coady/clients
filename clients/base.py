import collections
import contextlib
import functools
import random
import re
import threading
import requests
from requests.compat import json, urljoin

try:
    from future_builtins import map
except ImportError:  # pragma: no cover
    pass


def content_type(response, **patterns):
    """Return name for response's content-type based on regular expression matches."""
    ct = response.headers.get('content-type', '')
    matches = (name for name, pattern in patterns.items() if re.match(pattern, ct))
    return next(matches, '')


def validate(response):
    """Return validation headers from response translated for modification."""
    headers = response.headers
    validators = {'etag': 'if-match', 'last-modified': 'if-unmodified-since'}
    return {validators[key]: headers[key] for key in validators if key in headers}


class TokenAuth(dict):
    def __call__(self, req):
        req.headers['Authorization'] = ' '.join(*self.items())
        return req


class Client(requests.Session):
    """A Session which sends requests to a base url.

    :param url: base url for requests
    :param trailing: trailing chars (e.g. /) appended to the url
    :param headers: additional headers to include in requests
    :param auth: additional authorization support for ``{token_type: access_token}``,
        available per request as well
    :param attrs: additional Session attributes
    """

    def __init__(self, url, trailing='', headers=(), auth=None, **attrs):
        super(Client, self).__init__()
        self.__setstate__(attrs)
        self.auth = TokenAuth(auth) if isinstance(auth, dict) else auth
        self.headers.update(headers)
        self.trailing = trailing
        self.url = url.rstrip('/') + '/'

    @classmethod
    def clone(cls, other, path='', **kwargs):
        kwargs.update(other.__getstate__())
        return cls(urljoin(other.url, path), trailing=other.trailing, **kwargs)

    def __repr__(self):
        return '{}({}... {})'.format(type(self).__name__, self.url, self.trailing)

    def __truediv__(self, path):
        """Return a cloned client with appended path."""
        return type(self).clone(self, path)

    __div__ = __truediv__

    def request(self, method, path, auth=None, **kwargs):
        """Send request with relative or absolute path and return response."""
        kwargs['auth'] = TokenAuth(auth) if isinstance(auth, dict) else auth
        url = urljoin(self.url, path).rstrip('/') + self.trailing
        return super(Client, self).request(method, url, **kwargs)

    def get(self, path='', **kwargs):
        """GET request with optional path."""
        return self.request('GET', path, **kwargs)

    def options(self, path='', **kwargs):
        """OPTIONS request with optional path."""
        return self.request('OPTIONS', path, **kwargs)

    def head(self, path='', allow_redirects=False, **kwargs):
        """HEAD request with optional path."""
        return self.request('HEAD', path, allow_redirects=allow_redirects, **kwargs)

    def post(self, path='', json=None, **kwargs):
        """POST request with optional path and json body."""
        return self.request('POST', path, json=json, **kwargs)

    def put(self, path='', json=None, **kwargs):
        """PUT request with optional path and json body."""
        return self.request('PUT', path, json=json, **kwargs)

    def patch(self, path='', json=None, **kwargs):
        """PATCH request with optional path and json body."""
        return self.request('PATCH', path, json=json, **kwargs)

    def delete(self, path='', **kwargs):
        """DELETE request with optional path."""
        return self.request('DELETE', path, **kwargs)


class Resource(Client):
    """A `Client`_ which returns json content and has syntactic support for requests."""

    client = property(Client.clone, doc="upcasted `Client`_")
    __getitem__ = Client.get
    __setitem__ = Client.put
    __delitem__ = Client.delete
    content_type = functools.partial(content_type, text='text/', json=r'application/(\w|\.)*\+?json')

    def __getattr__(self, name):
        if name in type(self).__attrs__:
            raise AttributeError(name)
        return self / name

    __getattr__.__doc__ = Client.__truediv__.__doc__

    def request(self, method, path, **kwargs):
        """Send request with path and return processed content."""
        response = super(Resource, self).request(method, path, **kwargs)
        response.raise_for_status()
        if self.content_type(response) == 'json':
            return response.json()
        return response.text if response.encoding else response.content

    def iter(self, path='', **kwargs):
        """Iterate lines or chunks from streamed GET request."""
        response = super(Resource, self).request('GET', path, stream=True, **kwargs)
        response.raise_for_status()
        content_type = self.content_type(response)
        if content_type == 'json':
            response.encoding = response.encoding or 'utf8'
            return map(json.loads, response.iter_lines(decode_unicode=True))
        if response.encoding or content_type == 'text':
            return response.iter_lines(decode_unicode=response.encoding)
        return iter(response)

    __iter__ = iter

    def __contains__(self, path):
        """Return whether endpoint exists according to HEAD request."""
        return super(Resource, self).request('HEAD', path, allow_redirects=False).ok

    def __call__(self, path='', **params):
        """GET request with params."""
        return self.get(path, params=params)

    def updater(self, path='', **kwargs):
        response = super(Resource, self).request('GET', path, **kwargs)
        response.raise_for_status()
        kwargs['headers'] = dict(kwargs.get('headers', {}), **validate(response))
        yield self.put(path, (yield response.json()), **kwargs)

    @contextlib.contextmanager
    def updating(self, path='', **kwargs):
        """Provisional context manager to GET and conditionally PUT json data."""
        updater = self.updater(path, **kwargs)
        json = next(updater)
        yield json
        updater.send(json)

    def update(self, path='', callback=None, **json):
        """PATCH request with json params.

        :param callback: optionally update with GET and validated PUT.
            ``callback`` is called on the json result with keyword params, i.e.,
            ``dict`` correctly implements the simple update case.
        """
        if callback is None:
            return self.patch(path, json=json)
        updater = self.updater(path)
        return updater.send(callback(next(updater), **json))

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

    def authorize(self, path='', **kwargs):
        """Acquire oauth access token and set ``auth``."""
        method = 'GET' if {'json', 'data'}.isdisjoint(kwargs) else 'POST'
        result = self.request(method, path, **kwargs)
        self.auth = TokenAuth({result['token_type']: result['access_token']})
        return result


class Remote(Client):
    """A `Client`_ which defaults to posts with json bodies, i.e., RPC.

    :param url: base url for requests
    :param json: default json body for all calls
    :param kwargs: same options as `Client`_
    """

    client = Resource.client
    __getattr__ = Resource.__dict__['__getattr__']

    def __init__(self, url, json=(), **kwargs):
        super(Remote, self).__init__(url, **kwargs)
        self.json = dict(json)

    @classmethod
    def clone(cls, other, path=''):
        return Client.clone.__func__(cls, other, path, json=other.json)

    def __call__(self, path='', **json):
        """POST request with json body and :meth:`check` result."""
        response = self.post(path, json=dict(self.json, **json))
        response.raise_for_status()
        return self.check(response.json())

    @staticmethod
    def check(result):
        """Override to return result or raise error, for APIs which don't use status codes."""
        return result


class Graph(Remote):
    """A `Remote`_ client which executes GraphQL queries."""

    Error = requests.HTTPError

    @classmethod
    def check(cls, result):
        """Return ``data`` or raise ``errors``."""
        for error in result.get('errors', ()):
            raise cls.Error(error)
        return result.get('data')

    def execute(self, query, **variables):
        """Execute query over POST."""
        return self(query=query, variables=variables)


class Stats(collections.Counter):
    """Thread-safe Counter.

    Context manager tracks number of active connections and errors.
    """

    def __init__(self):
        self.lock = threading.Lock()

    def add(self, **kwargs):
        """Atomically add data."""
        with self.lock:
            self.update(kwargs)

    def __enter__(self):
        self.add(connections=1)
        return self

    def __exit__(self, *args):
        self.add(connections=-1, errors=int(any(args)))


class Proxy(Client):
    """An extensible embedded proxy client to multiple hosts.

    The default implementation provides load balancing based on active connections.
    It does not provide error handling or retrying.

    :param urls: base urls for requests
    :param kwargs: same options as `Client`_
    """

    Stats = Stats

    def __init__(self, *urls, **kwargs):
        super(Proxy, self).__init__('', **kwargs)
        self.urls = {(url.rstrip('/') + '/'): self.Stats() for url in urls}

    @classmethod
    def clone(cls, other, path=''):
        urls = (urljoin(url, path) for url in other.urls)
        return cls(*urls, trailing=other.trailing, **other.__getstate__())

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
        with self.urls[url] as stats:
            response = super(Proxy, self).request(method, urljoin(url, path), **kwargs)
        stats.add(failures=int(response.status_code >= 500))
        return response
