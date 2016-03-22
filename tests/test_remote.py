import io
import pytest
import clients


def test_cookies():
    client = clients.Client('http://httpbin.org/',
                            auth=('user', 'pass'), headers={'x-test': 'true'})
    r = client.get('headers', headers={'x-test2': 'true'})
    assert {'x-test', 'x-test2'} <= set(r.request.headers)

    r = client.get('cookies', cookies={'from-my': 'browser'})
    assert r.json() == {'cookies': {'from-my': 'browser'}}
    r = client.get('cookies')
    assert r.json() == {'cookies': {}}

    client.get('cookies/set', params={'sessioncookie': '123456789'})
    r = client.get('cookies')
    assert r.json() == {'cookies': {'sessioncookie': '123456789'}}


def test_content():
    resource = clients.Resource('http://httpbin.org/')
    assert resource.get('get')['url'] == 'http://httpbin.org/get'
    with pytest.raises(IOError):
        resource.get('status/404')
    assert '<html>' in resource.get('html')
    assert isinstance(resource.get('bytes/10'), bytes)


def test_path():
    client = clients.Client('http://httpbin.org/')
    cookies = client / 'cookies'
    assert isinstance(cookies, clients.Client)
    assert cookies.get().url == 'http://httpbin.org/cookies'

    assert cookies.get('/').url == 'http://httpbin.org/'
    assert cookies.get('http://httpbin.org/').url == 'http://httpbin.org/'


def test_trailing():
    client = clients.Client('http://httpbin.org/', trailing='/')
    assert client.get('ip').status_code == 404


def test_syntax():
    resource = clients.Resource('http://httpbin.org/')
    assert set(resource['get']) == {'origin', 'headers', 'args', 'url'}
    resource['put'] = {}
    del resource['delete']

    assert '200' in resource.status
    assert '404' not in resource.status
    assert [line['id'] for line in resource / 'stream/3'] == [0, 1, 2]
    assert next(iter(resource / 'html')) == '<!DOCTYPE html>'
    assert resource('cookies/set', name='value') == {'cookies': {'name': 'value'}}


def test_methods():
    resource = clients.Resource('http://httpbin.org/')
    assert list(map(len, resource.iter('stream-bytes/256'))) == [128] * 2
    assert resource.update('patch', name='value')['json'] == {'name': 'value'}
    assert resource.create('post', {'name': 'value'}) is None
    file = resource.download(io.BytesIO(), 'image/png')
    assert file.tell()
