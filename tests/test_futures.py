import pytest
asyncio = pytest.importorskip('asyncio')  # noqa
from concurrent import futures
from urllib.parse import urlparse
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
    assert isinstance(resource.client, clients.AsyncClient)
    it = results([resource['robots.txt'], resource.bytes('1'),
                  resource.update('patch', key='value'), resource.status('404')])
    assert isinstance(next(it), str)
    assert isinstance(next(it), bytes)
    assert next(it)['json'] == {'key': 'value'}
    with pytest.raises(aiohttp.ClientError):
        next(it)


def test_proxy():
    threader = futures.ThreadPoolExecutor(1)
    proxy = clients.Proxy(['http://httpbin.org/', 'https://httpbin.org/'])
    future = threader.submit(proxy.get, 'delay/0.1')
    response = proxy.get('status/500')
    assert not response.ok
    scheme = urlparse(future.result().url).scheme
    assert scheme != urlparse(response.url).scheme
    assert scheme == urlparse(proxy.get().url).scheme
