[![image](https://img.shields.io/pypi/v/clients.svg)](https://pypi.org/project/clients/)
[![image](https://img.shields.io/pypi/pyversions/clients.svg)](https://python3statement.org)
[![image](https://pepy.tech/badge/clients)](https://pepy.tech/project/clients)
![image](https://img.shields.io/pypi/status/clients.svg)
[![image](https://img.shields.io/travis/coady/clients.svg)](https://travis-ci.org/coady/clients)
[![image](https://img.shields.io/codecov/c/github/coady/clients.svg)](https://codecov.io/github/coady/clients)
[![image](https://readthedocs.org/projects/clients/badge)](https://clients.readthedocs.io)
[![image](https://requires.io/github/coady/clients/requirements.svg)](https://requires.io/github/coady/clients/requirements/)
[![image](https://api.codeclimate.com/v1/badges/8e4159e02ab75e76af4f/maintainability)](https://codeclimate.com/github/coady/clients/maintainability)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://pypi.org/project/black/)

Clients provide [requests](https://python-requests.org) and
[httpx](https://www.encode.io/httpx) wrappers which encourage best practices,
particularly always using Sessions to connect to the same host or api endpoint.

# Usage
Typical [requests](https://python-requests.org) usage is redundant and inefficient,
by not taking advantage of connection pooling.

```python
r = requests.get('https://api.github.com/user', headers={'authorization': token})
r = requests.get('https://api.github.com/user/repos', headers={'authorization': token})
```

Using sessions is the better approach,
but more verbose and in practice requires manual url joining.

```python
s = requests.Session()
s.headers['authorization'] = token
r = s.get('https://api.github.com/user')
r = s.get('https://api.github.com/user/repos')
```

## Client
Clients make using sessions easier, with implicit url joining.

```python
client = clients.Client('https://api.github.com/', headers={'authorization': token})
r = client.get('user')
r = client.get('user/repos')
```

## Resource
Resources extend Clients to implicitly handle response content,
with proper checking of status_code and content-type.

```python
github = clients.Resource('https://api.github.com/', headers={'authorization': token})
for repo in github.get('user/repos', params={'visibility': 'public'}):
    ...
```

Resources also implement syntactic support for methods such as __getattr__ and __call__,
providing most of the benefits of custom clients as is.

```python
for repo in github.user.repos(visibility='public'):
    ...
```

Being session based, Clients work seamlessly with other [requests](https://python-requests.org) adapters,
such as [CacheControl](https://cachecontrol.readthedocs.org).
Asynchronous variants of all client types are provided in [Python 3](https://python3statement.org),
using [httpx](https://www.encode.io/httpx) instead of [requests](https://python-requests.org).
Additional clients for [RPC](https://en.wikipedia.org/wiki/Remote_procedure_call),
[GraphQL](http://graphql.org), and proxies also provided.

# Installation

    $ pip install clients

# Dependencies
* requests >=2.4.2
* httpx >=0.8 (if Python >=3.6)

# Tests
100% branch coverage.

    $ pytest [--cov]

# Roadmap
`aiohttp` has made several incompatible changes, including forbidding subclassing.
So the async client has switched to `httpx`.

There are no interface changes to the async client itself, other than the different response object.
In the future `clients` may switch to only `httpx` or `requests3`.

# Changes
1.1
* Async switched to httpx

1.0
* Allow missing content-type
* Oauth access tokens supported in authorization header

0.5
* `AsyncClient` default params
* `Remote` and `AsyncRemote` procedure calls
* `Graph` and `AsyncGraph` execute GraphQL queries
* `Proxy` and `AsyncProxy` clients

0.4
* Asynchronous clients and resources

0.3
* `singleton` decorator

0.2
* Resource attribute upcasts back to a `client`
* `iter` and `download` implement GET requests with streamed content
* `create` implements POST request and returns Location header
* `update` implements PATCH request with json params
* `__call__` implements GET request with params
