# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased
### Changed
* Python >=3.10 required

## [1.5](https://pypi.org/project/clients/1.5/) - 2023-11-19
### Changed
* Python >=3.8 required
* httpx >=0.25 required

## [1.4](https://pypi.org/project/clients/1.4/) - 2022-11-19
### Changed
* Python >=3.7 required
* httpx >=0.23 required

### Removed
* `requests` removed

## [1.3](https://pypi.org/project/clients/1.3/) - 2020-11-24
* httpx >=0.15 required
* requests deprecated

## [1.2](https://pypi.org/project/clients/1.2/) - 2020-01-09
* Python 3 required
* httpx >=0.11 required

## [1.1](https://pypi.org/project/clients/1.1/) - 2019-12-07
* Async switched to httpx

## [1.0](https://pypi.org/project/clients/1.0/) - 2018-12-08
* Allow missing content-type
* Oauth access tokens supported in authorization header

## [0.5](https://pypi.org/project/clients/0.5/) - 2017-12-18
* `AsyncClient` default params
* `Remote` and `AsyncRemote` procedure calls
* `Graph` and `AsyncGraph` execute GraphQL queries
* `Proxy` and `AsyncProxy` clients

## [0.4](https://pypi.org/project/clients/0.4/) - 2017-06-11
* Asynchronous clients and resources

## [0.3](https://pypi.org/project/clients/0.3/) - 2017-01-02
* `singleton` decorator

## [0.2](https://pypi.org/project/clients/0.2/) - 2016-04-10
* Resource attribute upcasts back to a `client`
* `iter` and `download` implement GET requests with streamed content
* `create` implements POST request and returns Location header
* `update` implements PATCH request with json params
* `__call__` implements GET request with params
