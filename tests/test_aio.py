import asyncio
import json
import operator
import httpx
import pytest
import clients


def results(*coros):
    loop = asyncio.get_event_loop()
    fs = [asyncio.ensure_future(coro, loop=loop) for coro in coros]
    return map(loop.run_until_complete, fs)


def test_client():
    client = clients.AsyncClient('http://httpbin.org/', params={'q': 0})
    coros = (
        client.head(),
        client.options(),
        client.post('post'),
        client.put('put'),
        client.patch('patch'),
        client.delete('delete'),
    )
    for r in results(*coros):
        assert r.status_code == 200 and r.url.query == 'q=0'
    (r,) = results((client / 'ip').get(params={'q': 1}))
    assert set(r.json()) == {'origin'} and r.url.query == 'q=1'


def test_resource():
    params = {'etag': 'W/0', 'last-modified': 'now'}
    resource = clients.AsyncResource('http://httpbin.org/', params=params)
    it = results(
        resource['robots.txt'],
        resource.bytes('1'),
        resource.update('patch', key='value'),
        resource.status('404'),
        resource.update('response-headers', callback=dict, key='value'),
    )
    assert isinstance(next(it), str)
    assert isinstance(next(it), bytes)
    assert next(it)['json'] == {'key': 'value'}
    with pytest.raises(httpx.HTTPError, match='404'):
        next(it)
    with pytest.raises(httpx.HTTPError, match='405'):
        next(it)
    cm = resource.updating('response-headers')
    if hasattr(cm, '__aenter__'):
        (data,) = results(cm.__aenter__())
        assert data['etag'] == 'W/0'
        with pytest.raises(httpx.HTTPError, match='405'):
            (data,) = results(cm.__aexit__(None, None, None))


def test_content(url):
    resource = clients.AsyncResource(url)
    resource.content_type = lambda response: 'json'
    coro = resource.get('robots.txt')
    assert not hasattr(coro, '__aenter__')
    with pytest.raises(ValueError):
        (data,) = results(coro)


def test_authorize(url, monkeypatch):
    auth = '', ''
    resource = clients.AsyncResource(url, auth=auth)
    basic, token = results(resource.get('headers'), resource.get('headers', auth={'token': 'abc123'}))
    assert basic['headers']['Authorization'].startswith('Basic ')
    assert token['headers']['Authorization'] == 'token abc123'
    resource = clients.AsyncResource(url, auth={'token': 'abc123'})
    assert dict(resource.headers) == {} and resource.auth == {'token': 'abc123'}
    basic, token = results(resource.get('headers', auth=auth), resource.get('headers'))
    assert basic['headers']['Authorization'].startswith('Basic ')
    assert token['headers']['Authorization'] == 'token abc123'

    resource = clients.AsyncResource(url)
    future = asyncio.Future()
    future.set_result({'access_token': 'abc123', 'token_type': 'Bearer', 'expires_in': 0})
    monkeypatch.setattr(clients.AsyncResource, 'request', lambda *args, **kwargs: future)
    for key in ('params', 'data', 'json'):
        assert resource.run('authorize', **{key: {}}) == future.result()
        assert resource.auth == {'Bearer': 'abc123'}


def test_remote(url):
    remote = clients.AsyncRemote(url, json={'key': 'value'})
    (result,) = results(remote('post'))
    assert result['json'] == {'key': 'value'}
    clients.AsyncRemote.check = operator.methodcaller('pop', 'json')
    (result,) = results((remote / 'post')(name='value'))
    assert result == {'key': 'value', 'name': 'value'}


def test_graph(url):
    graph = clients.AsyncGraph(url).anything
    (data,) = results(graph.execute('{ viewer { login }}'))
    assert json.loads(data) == {'query': '{ viewer { login }}', 'variables': {}}
    with pytest.raises(httpx.HTTPError, match='reason'):
        clients.AsyncGraph.check({'errors': ['reason']})


def test_proxy(url):
    proxy = clients.AsyncProxy(url, 'http://httpbin.org/')
    responses = results(*(proxy.get('get') for _ in proxy.urls))
    urls = {response.url: response.json() for response in responses}
    assert len(urls) == len(proxy.urls)
    assert all(urls.values())

    fs = (proxy.get('status/500') for _ in proxy.urls)
    (response,) = results(next(fs))
    assert next(results(*fs)).url != response.url

    proxy = clients.AsyncProxy('http://localhost/', 'http://httpbin.org/')
    with pytest.raises(OSError):
        list(results(*(proxy.get() for _ in proxy.urls)))
    (response,) = results(proxy.get())
    assert response.status_code == 200


def test_clones():
    client = clients.AsyncClient('http://localhost/', trailing='/')
    assert str(client) == 'AsyncClient(http://localhost/... /)'
    assert str(client / 'path') == 'AsyncClient(http://localhost/path/... /)'

    resource = clients.AsyncResource('http://localhost/').path
    assert str(resource) == 'AsyncResource(http://localhost/path/... )'
    assert type(resource.client) is clients.AsyncClient

    remote = clients.AsyncRemote('http://localhost/').path
    assert str(remote) == 'AsyncRemote(http://localhost/path/... )'
    assert type(remote.client) is clients.AsyncClient

    proxy = clients.AsyncProxy('http://localhost/', 'http://127.0.0.1') / 'path'
    assert str(proxy) == 'AsyncProxy(https://proxies/... )'
