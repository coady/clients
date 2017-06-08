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

    def __div__(self, path):
        """Return a cloned `Client`_ with appended path."""
        return type(self).clone(self, path)
    __truediv__ = __div__

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
