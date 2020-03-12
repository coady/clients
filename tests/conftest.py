import pytest
import requests
import httpx

pytest_plugins = ('httpbin',)


def pytest_report_header(config):
    modules = requests, httpx
    return ', '.join(f'{module.__name__} {module.__version__}' for module in modules)


@pytest.fixture
def url(httpbin):
    return httpbin.url
