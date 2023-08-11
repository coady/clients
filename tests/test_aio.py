import asyncio
import json
import operator
import httpx
import pytest
import clients


@pytest.mark.asyncio
async def test_client(url):
    client = clients.AsyncClient(url, params={'q': 0})
    coros = (
        client.head(),
        client.options(),
        client.post('post'),
        client.put('put'),
        client.patch('patch'),
        client.delete('delete'),
    )
    for coro in coros:
        r = await coro
        assert r.status_code == 200 and r.url.query == b'q=0'
    r = await (client / 'ip').get(params={'q': 1})
    assert set(r.json()) == {'origin'} and r.url.query == b'q=1'


@pytest.mark.asyncio
async def test_resource(url):
    params = {'etag': 'W/0', 'last-modified': 'now'}
    resource = clients.AsyncResource(url, params=params)
    assert isinstance(await resource['encoding/utf8'], str)
    assert isinstance(await resource('stream-bytes/1'), (str, bytes))
    assert (await resource.update('patch', key='value'))['json'] == {'key': 'value'}
    with pytest.raises(httpx.HTTPError, match='404'):
        await resource.status('404')
    with pytest.raises(httpx.HTTPError):
        await resource.update('response-headers', callback=dict, key='value')
    with pytest.raises(httpx.HTTPError):
        async with resource.updating('response-headers') as data:
            assert data['etag'] == 'W/0'


@pytest.mark.asyncio
async def test_content(url):
    resource = clients.AsyncResource(url)
    resource.content_type = lambda response: 'json'
    coro = resource.get('robots.txt')
    assert not hasattr(coro, '__aenter__')
    with pytest.raises(ValueError):
        await coro


def test_authorize(url, monkeypatch):
    resource = clients.AsyncResource(url)
    future = asyncio.Future(loop=asyncio.new_event_loop())
    future.set_result({'access_token': 'abc123', 'token_type': 'Bearer', 'expires_in': 0})
    monkeypatch.setattr(clients.AsyncResource, 'request', lambda *args, **kwargs: future)
    for key in ('params', 'data', 'json'):
        assert resource.run('authorize', **{key: {}}) == future.result()
        assert resource.headers['authorization'] == 'Bearer abc123'


@pytest.mark.asyncio
async def test_remote(url):
    remote = clients.AsyncRemote(url, json={'key': 'value'})
    assert (await remote('post'))['json'] == {'key': 'value'}
    clients.AsyncRemote.check = operator.methodcaller('pop', 'json')
    assert await (remote / 'post')(name='value') == {'key': 'value', 'name': 'value'}


@pytest.mark.asyncio
async def test_graph(url):
    graph = clients.AsyncGraph(url).anything
    data = await graph.execute('{ viewer { login }}')
    assert json.loads(data) == {'query': '{ viewer { login }}', 'variables': {}}
    with pytest.raises(httpx.HTTPError, match='reason'):
        clients.AsyncGraph.check({'errors': ['reason']})


@pytest.mark.asyncio
async def test_proxy(httpbin):
    proxy = clients.AsyncProxy(httpbin.url, f'http://localhost:{httpbin.port}')
    urls = {(await proxy.get('status/500')).url for _ in proxy.urls}
    assert len(urls) == len(proxy.urls)


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
