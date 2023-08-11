import json
import operator
import io
import httpx
import pytest
import clients


def test_cookies(url):
    client = clients.Client(url, auth=('user', 'pass'), headers={'x-test': 'true'})
    r = client.get('headers', headers={'x-test2': 'true'})
    assert {'x-test', 'x-test2'} <= set(r.request.headers)

    r = client.get('cookies')
    assert r.json() == {'cookies': {}}

    client.get('cookies/set', params={'sessioncookie': '123456789'})
    r = client.get('cookies')
    assert r.json() == {'cookies': {'sessioncookie': '123456789'}}


def test_content(url):
    resource = clients.Resource(url)
    assert resource.get('get')['url'] == url + '/get'
    with pytest.raises(httpx.HTTPError):
        resource.get('status/404')
    assert '<html>' in resource.get('html')
    assert isinstance(resource.get('stream-bytes/10'), bytes)


def test_path(url):
    client = clients.Client(url)
    cookies = client / 'cookies'
    assert isinstance(cookies, clients.Client)
    assert str(cookies.get().url) == url + '/cookies'

    assert str(cookies.get('/').url) == url
    assert str(cookies.get(url).url) == url


def test_trailing(url):
    client = clients.Client(url, trailing='/')
    assert client.get('ip').status_code == 404


def test_syntax(url):
    resource = clients.Resource(url, follow_redirects=True)
    assert set(resource['get']) == {'origin', 'headers', 'args', 'url'}
    resource['put'] = {}
    del resource['delete']

    assert '200' in resource.status
    assert '404' not in resource.status
    assert [line['id'] for line in resource / 'stream/3'] == [0, 1, 2]
    assert next(iter(resource / 'html')) == '<!DOCTYPE html>'
    assert resource('cookies/set', name='value') == {'cookies': {'name': 'value'}}


def test_methods(url):
    resource = clients.Resource(url)
    assert sum(map(len, resource.stream(path='stream-bytes/256'))) == 256
    assert resource.update('patch', name='value')['json'] == {'name': 'value'}
    assert resource.create('post', {'name': 'value'}) is None
    file = resource.download(io.BytesIO(), 'image/png')
    assert file.tell()


def test_authorize(url, monkeypatch):
    resource = clients.Resource(url)
    result = {'access_token': 'abc123', 'token_type': 'Bearer', 'expires_in': 0}
    monkeypatch.setattr(clients.Resource, 'request', lambda *args, **kwargs: result)
    for key in ('params', 'data', 'json'):
        assert resource.authorize(**{key: {}}) == result
        assert resource.headers['authorization'] == 'Bearer abc123'


def test_callback(url):
    resource = clients.Resource(url, params={'etag': 'W/0', 'last-modified': 'now'})
    with pytest.raises(httpx.HTTPError, match='405') as exc:
        resource.update('response-headers', callback=dict, name='value')
    headers = exc.value.request.headers
    assert headers['if-match'] == 'W/0' and headers['if-unmodified-since'] == 'now'
    with pytest.raises(httpx.HTTPError, match='405') as exc:
        with resource.updating('response-headers') as data:
            data['name'] = 'value'
    assert b'"name": "value"' in exc.value.request.read()


def test_meta(url):
    client = clients.Client(url)
    response = client.options('get')
    assert not response.is_error and not response.content
    response = client.head('get')
    assert not response.is_error and not response.content
    del response.headers['content-type']
    assert clients.Resource.content_type(response) == ''


def test_remote(url):
    remote = clients.Remote(url, json={'key': 'value'})
    assert remote('post')['json'] == {'key': 'value'}
    clients.Remote.check = operator.methodcaller('pop', 'json')
    assert (remote / 'post')(name='value') == {'key': 'value', 'name': 'value'}


def test_graph(url):
    graph = clients.Graph(url).anything
    data = graph.execute('{ viewer { login }}')
    assert json.loads(data) == {'query': '{ viewer { login }}', 'variables': {}}
    with pytest.raises(httpx.HTTPError, match='reason'):
        clients.Graph.check({'errors': ['reason']})


def test_proxy(httpbin):
    proxy = clients.Proxy(httpbin.url, f'http://localhost:{httpbin.port}')
    urls = {proxy.get('status/500').url for _ in proxy.urls}
    assert len(urls) == len(proxy.urls)


def test_clones():
    client = clients.Client('http://localhost/', trailing='/')
    assert str(client) == 'Client(http://localhost/... /)'
    assert str(client / 'path') == 'Client(http://localhost/path/... /)'

    resource = clients.Resource('http://localhost/').path
    assert str(resource) == 'Resource(http://localhost/path/... )'
    assert type(resource.client) is clients.Client

    remote = clients.Remote('http://localhost/').path
    assert str(remote) == 'Remote(http://localhost/path/... )'
    assert type(remote.client) is clients.Client

    proxy = clients.Proxy('http://localhost/', 'http://127.0.0.1') / 'path'
    assert str(proxy) == 'Proxy(https://proxies/... )'


def test_singleton():
    @clients.singleton('http://localhost/')
    class custom_api(clients.Resource):
        pass  # custom methods

    assert isinstance(custom_api, clients.Resource)
    assert custom_api.url == 'http://localhost/'
