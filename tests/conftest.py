import json
import pytest
import requests


def pytest_report_header(config):
    return 'Requests ' + requests.__version__


def request(self, method, url, status_code=200, allow_redirects=True, stream=False, **kwargs):
    if status_code is None:
        raise IOError
    response = requests.Response()
    content = json.dumps(kwargs.get('json', {})).encode('utf8')
    response.__setstate__({'url': url, '_content': content, 'status_code': status_code})
    response.request = requests.PreparedRequest()
    response.request.prepare(method, url, hooks=(), **kwargs)
    accept = self.headers['accept']
    response.headers['content-type'] = 'application/json' if accept == '*/*' else accept
    if accept.startswith('text/'):
        response.encoding = 'utf8'
    if method == 'POST':
        response.headers['location'] = url + '/id'
    return response


@pytest.fixture
def local(monkeypatch):
    monkeypatch.setattr('requests.Session.request', request)
