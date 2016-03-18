import pytest
import requests


def pytest_report_header(config):
    return 'Requests ' + requests.__version__


def request(self, method, url, params=None, json=None, **kwargs):
    response = requests.Response()
    response.__setstate__({'method': method, 'url': url, '_content': b'{}', 'status_code': 200})
    response.request = requests.PreparedRequest()
    response.request.prepare(method, url, params=params, json=json, hooks=())
    accept = self.headers['accept']
    response.headers['content-type'] = 'application/json' if accept == '*/*' else accept
    return response


@pytest.fixture
def local(monkeypatch):
    monkeypatch.setattr('requests.Session.request', request)
