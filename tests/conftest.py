import pytest
import httpx

pytest_plugins = ('httpbin',)


def pytest_report_header(config):
    return f'httpx {httpx.__version__}'


@pytest.fixture
def url(httpbin):
    return httpbin.url
