import io
import pytest
import requests
import clients

url = 'http://localhost/'
methods = 'get', 'options', 'head', 'post', 'put', 'patch', 'delete'


def test_client(local):
    client = clients.Client(url, trailing='/')
    assert isinstance(client, requests.Session)
    for method in methods:
        response = getattr(client, method)()
        assert isinstance(response, requests.Response)
        assert response.url == url
        assert response.request.method == method.upper()

    client = clients.Client(url, headers={'Authorization': 'token'}, stream=True)
    assert client.stream
    assert client.headers.pop('authorization') == 'token'
    assert client.headers

    client /= 'path'
    assert client.get().url.endswith('path')


def test_resource(local):
    with pytest.raises(AttributeError):
        clients.Resource(url).prefetch
    resource = clients.Resource(url).path
    assert isinstance(resource, clients.Client)
    assert type(resource.client) is clients.Client

    assert resource[''] == resource.get() == {}
    resource['enpoint'] = {}
    del resource['endpoint']
    assert 'endpoint' in resource
    assert list(resource) == [{}]
    assert resource(name='value') == {}
    assert resource.update(name='value') == {}
    assert resource.create(json={'name': 'value'}).endswith('/id')

    resource.headers['accept'] = 'application/octet-stream'
    assert resource.get() == b'{}'
    assert list(resource) == [b'{}']

    resource.headers['accept'] = 'text/html'
    assert resource.get() == '{}'
    assert list(resource) == ['{}']

    file = resource.download(io.BytesIO())
    assert file.tell() == 2


def test_singleton():
    @clients.singleton(url)
    class custom_api(clients.Resource):
        pass  # custom methods

    assert isinstance(custom_api, clients.Resource)
    assert custom_api.url == url
