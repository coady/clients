import pytest
import requests

pytest_plugins = 'httpbin',


def pytest_report_header(config):
    return 'Requests ' + requests.__version__


@pytest.fixture
def url(httpbin):
    return httpbin.url
