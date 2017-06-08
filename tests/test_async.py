import pytest
asyncio = pytest.importorskip('asyncio')
from clients import AsyncClient  # noqa


def results(coros):
    loop = asyncio.get_event_loop()
    fs = [asyncio.ensure_future(coro, loop=loop) for coro in coros]
    return map(loop.run_until_complete, fs)


def test_client():
    client = AsyncClient('http://httpbin.org/')
    coros = (client.head(), client.options(), client.post('post'), client.put('put'),
             client.patch('patch'), client.delete('delete'), (client / 'ip').get())
    for r in results(coros):
        assert r.status == 200
    data, = results([r.json()])
    assert set(data) == {'origin'}
