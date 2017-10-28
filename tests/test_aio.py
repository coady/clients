import operator
import pytest
asyncio = pytest.importorskip('asyncio')  # noqa
import aiohttp
import clients


def results(coros):
    loop = asyncio.get_event_loop()
    fs = list(map(loop.create_task, coros))
    return map(loop.run_until_complete, fs)


def test_client():
    client = clients.AsyncClient('http://httpbin.org/', params={'q': 0})
    coros = (client.head(), client.options(), client.post('post'), client.put('put'),
             client.patch('patch'), client.delete('delete'), (client / 'ip').get(params={'q': 1}))
    for r in results(coros):
        assert r.status == 200 and r.url.query_string.endswith('q=0')
    assert r.url.query_string == 'q=1&q=0'
    data, = results([r.json()])
    assert set(data) == {'origin'}


def test_resource():
    resource = clients.AsyncResource('http://httpbin.org/')
    it = results([resource['robots.txt'], resource.bytes('1'),
                  resource.update('patch', key='value'), resource.status('404')])
    assert isinstance(next(it), str)
    assert isinstance(next(it), bytes)
    assert next(it)['json'] == {'key': 'value'}
    with pytest.raises(aiohttp.ClientError):
        next(it)


def test_remote(url):
    remote = clients.AsyncRemote(url, json={'key': 'value'})
    result, = results([remote('post')])
    assert result['json'] == {'key': 'value'}
    clients.AsyncRemote.check = operator.methodcaller('pop', 'json')
    result, = results([(remote / 'post')(name='value')])
    assert result == {'key': 'value', 'name': 'value'}


def test_proxy(httpbin):
    proxy = clients.AsyncProxy([httpbin.url, 'http://localhost:{}'.format(httpbin.port)])
    it = results([proxy.get('delay/0.1'), proxy.get('status/500')])
    host = next(it).url.host
    assert host != next(it).url.host
    response, = results([proxy.get()])
    assert host == response.url.host


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

    proxy = clients.AsyncProxy(['http://localhost/', 'http://127.0.0.1']) / 'path'
    assert str(proxy) == 'AsyncProxy(/... )'
