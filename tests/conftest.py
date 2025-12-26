from importlib import metadata

import pytest


def pytest_report_header(config):
    return "httpx: " + metadata.version("httpx")


@pytest.fixture
def url(httpbin):
    return httpbin.url
