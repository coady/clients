import pytest
import requests
import clients

aio = getattr(clients, 'aio', None)
pytest_plugins = ('httpbin',)


def pytest_ignore_collect(path, config):
    return not aio and path.basename == 'test_aio.py'


def pytest_report_header(config):
    modules = {requests, getattr(aio, 'httpx', requests)}
    return ', '.join('{} {}'.format(module.__name__, module.__version__) for module in modules)


@pytest.fixture
def url(httpbin):
    return httpbin.url
