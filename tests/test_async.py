import pytest
asyncio = pytest.importorskip('asyncio')  # noqa
import aiohttp
from clients import AsyncClient, AsyncResource


def results(coros):
    loop = asyncio.get_event_loop()
    fs = list(map(loop.create_task, coros))
    return map(loop.run_until_complete, fs)


def test_client():
    client = AsyncClient('http://httpbin.org/')
    coros = (client.head(), client.options(), client.post('post'), client.put('put'),
             client.patch('patch'), client.delete('delete'), (client / 'ip').get())
    for r in results(coros):
        assert r.status == 200
    data, = results([r.json()])
    assert set(data) == {'origin'}


def test_resource():
    resource = AsyncResource('http://httpbin.org/')
    assert isinstance(resource.client, AsyncClient)
    it = results([resource['robots.txt'], resource.bytes('1'),
                  resource.update('patch', key='value'), resource.status('404')])
    assert isinstance(next(it), str)
    assert isinstance(next(it), bytes)
    assert next(it)['json'] == {'key': 'value'}
    with pytest.raises(aiohttp.ClientError):
        next(it)
