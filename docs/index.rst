.. Clients documentation master file, created by sphinx-quickstart.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Clients' documentation.
==================================
HTTP for lazy, impatient, hubristic humans.

Quickstart
^^^^^^^^^^
As great as `requests`_ is, typical usage is falling into some anti-patterns.

   * Being url-based, realistically all code needs to deal with url joining.
     Which tends to be redundant and suffer from leading or trailing slash issues.
   * The module level methods don't take advantage of connection pooling, and require duplicate settings.
     Given the "100% automatic" documentation of connection reuse, it's unclear how widely known this is.
   * Using `Sessions`_ requires assigning every setting individually, and still requires url joining.

`Clients <reference.html#client>`_ aim to be encourage best practices by making Sessions even easier to use than the module methods.

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_cookies
   :start-after: cookies
   :dedent: 4

Which reveals another anti-pattern regarding `Responses`_.  Although the response object is sometimes required,
naturally the most common use case is to access the content.  But the onus is on the caller to check the
``status_code`` and ``content-type``.

`Resources <reference.html#resource>`_ aim to making writing custom api clients or sdks easier.
Their primary feature is to allow direct content access without silencing errors.
Response content type is inferred from headers: ``json``, ``content``, or ``text``.

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_content
   :start-after: content
   :dedent: 4

Advanced Usage
^^^^^^^^^^^^^^
``Clients`` allow any base url, not just hosts, and consequently support path concatenation.
Following the semantics of ``urljoin`` however, absolute paths and urls are treated as such.
Hence there's no need to parse a url retrieved from an api.

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_path
   :start-after: path
   :dedent: 4

Some api endpoints require trailing slashes; some forbid them.  Set it and forget it.

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_trailing
   :start-after: trailing
   :dedent: 4

Note ``trailing`` doesn't technically have to be a slash.  This can be useful for static paths below a parameter:
``.../<user>/profile``.

Avant-garde Usage
^^^^^^^^^^^^^^^^^
.. note::
   These experimental interfaces may obviate the need for custom clients altogether.

``Resources`` support operator overloaded syntax wherever sensible.

   * ``__getattr__``: alternate path concatenation
   * ``__getitem__``: GET content
   * ``__setitem__``: PUT json
   * ``__delitem__``: DELETE
   * ``__contains__``: HEAD ok
   * ``__iter__``: GET streamed lines or content
   * ``__call__``: GET with params

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_syntax
   :start-after: syntax
   :dedent: 4

Higher-level methods for common requests.

   * ``iter``: __iter__ with args
   * ``update``: PATCH with json params
   * ``create``: POST and return location
   * ``download``: GET streamed content to file

.. literalinclude:: ../tests/test_remote.py
   :pyobject: test_methods
   :start-after: methods
   :dedent: 4

A `singleton <reference.html#singleton>`_ decorator can be used on subclasses,
conveniently creating a single custom instance.

.. literalinclude:: ../tests/test_local.py
   :pyobject: test_singleton
   :start-after: singleton
   :dedent: 4

Contents:
==================
.. toctree::
   :maxdepth: 1

   reference

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _requests: https://python-requests.org
.. _Sessions: http://docs.python-requests.org/en/master/user/advanced/#session-objects
.. _Responses: http://docs.python-requests.org/en/master/user/quickstart/#response-content
