## Quickstart

Typical [requests](https://python-requests.org) usage has falling into some anti-patterns.

* Being url-based, realistically all code needs to deal with url joining. Which tends to be redundant and suffer from leading or trailing slash issues.
* The module level methods don't take advantage of connection pooling, and require duplicate settings. Given the "100% automatic" documentation of connection reuse, it's unclear how widely known this is.
* Using a `Session` requires assigning every setting individually, and still requires url joining.

[Clients](reference.md#clients.Client) aim to be encourage best practices while still being convenient. Examples use the [httpbin](http://httpbin.org) client testing service.

```python
client = clients.Client(url, auth=('user', 'pass'), headers={'x-test': 'true'})
r = client.get('headers', headers={'x-test2': 'true'})
assert {'x-test', 'x-test2'} <= set(r.request.headers)

r = client.get('cookies', cookies={'from-my': 'browser'})
assert r.json() == {'cookies': {'from-my': 'browser'}}
r = client.get('cookies')
assert r.json() == {'cookies': {}}

client.get('cookies/set', params={'sessioncookie': '123456789'})
r = client.get('cookies')
assert r.json() == {'cookies': {'sessioncookie': '123456789'}}
```

Which reveals another anti-pattern regarding `Response` objects. Although the response object is sometimes required, naturally the most common use case is to access the content. But the onus is on the caller to check the `status_code` and `content-type`.

[Resources](reference.md#clients.Resource) aim to making writing custom api clients or sdks easier. Their primary feature is to allow direct content access without silencing errors. Response content type is inferred from headers: `json`, `content`, or `text`.

```python
resource = clients.Resource(url)
assert resource.get('get')['url'] == url + '/get'
with pytest.raises(IOError):
    resource.get('status/404')
assert '<html>' in resource.get('html')
assert isinstance(resource.get('bytes/10'), bytes)
```

## Advanced Usage

`Clients` allow any base url, not just hosts, and consequently support path concatenation. Following the semantics of `urljoin` however, absolute paths and urls are treated as such. Hence there's no need to parse a url retrieved from an api.

```python
client = clients.Client(url)
cookies = client / 'cookies'
assert isinstance(cookies, clients.Client)
assert cookies.get().url == url + '/cookies'

assert cookies.get('/').url == url + '/'
assert cookies.get(url).url == url + '/'
```

Some api endpoints require trailing slashes; some forbid them. Set it and forget it.

```python
client = clients.Client(url, trailing='/')
assert client.get('ip').status_code == 404
```

Note `trailing` isn\'t limited to only being a slash. This can be useful for static paths below a parameter: `api/v1/{query}.json`.

## Asyncio

[AsyncClients](reference.md#clients.AsyncClient) and [AsyncResources](reference.md#clients.AsyncResource) implement the same interface, except the request methods return asyncio [coroutines](https://docs.python.org/3/library/asyncio-task.html#coroutines).

## Avant-garde Usage

`Resources` support operator overloaded syntax wherever sensible. These interfaces often obviate the need for writing custom clients specific to an API.

* `__getattr__`: alternate path concatenation
* `__getitem__`: GET content
* `__setitem__`: PUT json
* `__delitem__`: DELETE
* `__contains__`: HEAD ok
* `__iter__`: GET streamed lines or content
* `__call__`: GET with params

```python
resource = clients.Resource(url)
assert set(resource['get']) == {'origin', 'headers', 'args', 'url'}
resource['put'] = {}
del resource['delete']

assert '200' in resource.status
assert '404' not in resource.status
assert [line['id'] for line in resource / 'stream/3'] == [0, 1, 2]
assert next(iter(resource / 'html')) == '<!DOCTYPE html>'
assert resource('cookies/set', name='value') == {'cookies': {'name': 'value'}}
```

Higher-level methods for common requests.

* `iter`: \_\_iter\_\_ with args
* `update`: PATCH with json params, or GET with conditional PUT
* `create`: POST and return location
* `download`: GET streamed content to file
* `authorize`: acquire oauth token

```python
resource = clients.Resource(url)
assert list(map(len, resource.iter('stream-bytes/256'))) == [128] * 2
assert resource.update('patch', name='value')['json'] == {'name': 'value'}
assert resource.create('post', {'name': 'value'}) is None
file = resource.download(io.BytesIO(), 'image/png')
assert file.tell()
```

A [singleton](reference.md#clients.singleton) decorator can be used on subclasses, conveniently creating a single custom instance.

```python
@clients.singleton('http://localhost/')
class custom_api(clients.Resource):
    pass  # custom methods

assert isinstance(custom_api, clients.Resource)
assert custom_api.url == 'http://localhost/'
```

[Remote](reference.md#clients.Remote) and [AsyncRemote](reference.md#clients.AsyncRemote) clients default to POSTs with json bodies, for APIs which are more RPC than REST.

[Graph](reference.md#clients.Graph) and [AsyncGraph](reference.md#clients.AsyncGraph) remote clients execute GraphQL queries.

[Proxy](reference.md#clients.Proxy) and [AsyncProxy](reference.md#clients.AsyncProxy) clients provide load-balancing across multiple hosts, with an extensible interface for different algorithms.
