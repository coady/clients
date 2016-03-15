import pytest
import requests
from clients import Client, Resource

url = 'http://localhost/'
methods = 'get', 'options', 'head', 'post', 'put', 'patch', 'delete'


def test_client(local):
    client = Client(url, trailing='/')
    assert isinstance(client, requests.Session)
    for method in methods:
        response = getattr(client, method)()
        assert isinstance(response, requests.Response)
        assert response.url == url
        assert response.request.method == method.upper()

    client = Client(url, headers={'Authorization': 'token'}, stream=True)
    assert client.stream
    assert client.headers.pop('authorization') == 'token'
    assert client.headers

    client /= 'path'
    assert client.get().url.endswith('path')


def test_resource(local):
    with pytest.raises(AttributeError):
        Resource(url).prefetch
    resource = Resource(url).path
    assert isinstance(resource, Client)

    assert resource[''] == resource.get() == {}
    resource['enpoint'] = {}
    del resource['endpoint']
    assert 'endpoint' in resource
    assert list(resource) == [{}]

    resource.headers['accept'] = 'text/html'
    assert resource.get() == b'{}'
    assert list(resource) == [b'{}']
