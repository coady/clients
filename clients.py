import requests
json = requests.compat.json
urljoin = requests.compat.urljoin

__version__ = '0.1'


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

    def __div__(self, path):
        """Return a cloned `Client`_ with appended path."""
        return type(self)(urljoin(self.url, path), self.trailing, **self.__getstate__())
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
    __getitem__ = Client.get
    __setitem__ = Client.put
    __delitem__ = Client.delete

    def __iter__(self):
        """Iterate lines from streamed GET request."""
        response = super(Resource, self).request('GET', '', stream=True)
        response.raise_for_status()
        lines = response.iter_lines()
        if response.headers['content-type'].startswith('application/json'):
            return (json.loads(line.decode('utf8')) for line in lines)
        return lines

    def __contains__(self, path):
        """Return whether endpoint exists according to HEAD request."""
        return super(Resource, self).request('HEAD', path)

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
        return response.content
