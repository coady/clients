.. image:: https://img.shields.io/pypi/v/clients.svg
   :target: https://pypi.org/project/clients/
.. image:: https://img.shields.io/pypi/pyversions/clients.svg
.. image:: https://img.shields.io/pypi/status/clients.svg
.. image:: https://img.shields.io/travis/coady/clients.svg
   :target: https://travis-ci.org/coady/clients
.. image:: https://img.shields.io/codecov/c/github/coady/clients.svg
   :target: https://codecov.io/github/coady/clients
.. image:: https://readthedocs.org/projects/clients/badge
   :target: `documentation`_

Clients provide `requests`_ and `aiohttp`_ wrappers which encourage best practices,
particularly always using Sessions to connect to the same host or api endpoint.

Usage
=========================
Typical `requests`_ usage is redundant and inefficient, by not taking advantage of connection pooling.

.. code-block:: python

   r = requests.get('https://api.github.com/user', headers={'authorization': token})
   r = requests.get('https://api.github.com/user/repos', headers={'authorization': token})

Using sessions is the better approach, but more verbose and in practice requires manual url joining.

.. code-block:: python

   s = requests.Session()
   s.headers['authorization'] = token
   r = s.get('https://api.github.com/user')
   r = s.get('https://api.github.com/user/repos')

Clients make using sessions easier, with implicit url joining.

.. code-block:: python

   client = clients.Client('https://api.github.com/', headers={'authorization': token})
   r = client.get('user')
   r = client.get('user/repos')

Resources extend Clients to implicitly handle response content, with proper checking of `status_code` and `content-type`.

.. code-block:: python

   github = clients.Resource('https://api.github.com/', headers={'authorization': token})
   for repo in github.get('user/repos', params={'visibility': 'public'}):
      ...

Resources also implement syntactic support for methods such as `__getattr__` and `__call__`,
providing most of the benefits of custom clients, without having to define a schema.

.. code-block:: python

   for repo in github.user.repos(visibility='public'):
      ...

Being session based, Clients work seamlessly with other `requests`_ adapters, such as `CacheControl`_.
Asynchronous variants of all client types are provided in Python >=3.5, using `aiohttp`_ instead of `requests`_.
Additional clients for `RPC`_, `GraphQL`_, and proxies also provided.

Read the `documentation`_.

Installation
=========================
::

   $ pip install clients

Dependencies
=========================
* requests >=2.4.2
* aiohttp (if Python >=3.5)

Tests
=========================
100% branch coverage. ::

   $ pytest [--cov]

Changes
=========================
dev

* ``AsyncClient`` default params
* ``Remote`` and ``AsyncRemote`` procedure calls
* ``Graph`` and ``AsyncGraph`` execute GraphQL queries
* ``Proxy`` and ``AsyncProxy`` clients

0.4

* Asynchronous clients and resources

0.3

* ``singleton`` decorator

0.2

* Resource attribute upcasts back to a ``client``
* ``iter`` and ``download`` implement GET requests with streamed content
* ``create`` implements POST request and returns Location header
* ``update`` implements PATCH request with json params
* ``__call__`` implements GET request with params

.. _requests: https://python-requests.org
.. _aiohttp: http://aiohttp.readthedocs.io
.. _documentation: http://clients.readthedocs.io
.. _CacheControl: https://cachecontrol.readthedocs.org
.. _RPC: https://en.wikipedia.org/wiki/Remote_procedure_call
.. _GraphQL: http://graphql.org
