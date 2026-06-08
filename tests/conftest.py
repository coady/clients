from importlib import metadata

import pytest


def pytest_report_header(config):
    return "httpx2: " + metadata.version("httpx2")


@pytest.fixture
def url(httpbin):
    return httpbin.url
