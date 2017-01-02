.. image:: https://img.shields.io/pypi/v/clients.svg
   :target: https://pypi.python.org/pypi/clients/
.. image:: https://img.shields.io/pypi/pyversions/clients.svg
.. image:: https://img.shields.io/pypi/status/clients.svg
.. image:: https://img.shields.io/travis/coady/clients.svg
   :target: https://travis-ci.org/coady/clients
.. image:: https://img.shields.io/codecov/c/github/coady/clients.svg
   :target: https://codecov.io/github/coady/clients

Clients provide `requests`_ wrappers which encourage best practices,
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

   resource = clients.Resource('https://api.github.com/', headers={'authorization': token})
   for repo in resource.get('user/repos'):
      ...

Being session based, Clients also work seamlessly with other `requests`_ adapters, such as `CacheControl`_.

See `documentation`_ for more examples.

Installation
=========================
::

   $ pip install clients

Dependencies
=========================
* Requests 2.4.2+
* Python 2.7, 3.3+

Tests
=========================
100% branch coverage. ::

   $ pytest [--cov]

Changes
=========================
0.3

* ``singleton`` decorator

0.2

* Resource attribute upcasts back to a ``client``
* ``iter`` and ``download`` implement GET requests with streamed content
* ``create`` implements POST request and returns Location header
* ``update`` implements PATCH request with json params
* ``__call__`` implements GET request with params

.. _requests: https://python-requests.org
.. _documentation: http://pythonhosted.org/clients/
.. _CacheControl: https://cachecontrol.readthedocs.org/en/latest/
