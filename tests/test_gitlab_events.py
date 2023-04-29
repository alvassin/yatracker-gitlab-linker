from http import HTTPStatus

import pytest
from aiohttp import ClientSession
from yarl import URL

from yatracker_linker.service import HttpService
from yatracker_linker.st_client import StClient
from yatracker_linker.views.events import GITLAB_TOKEN_HEADER


class StClientMock(StClient):
    async def issue_exists(self, key: str):
        return True

    async def link_issue(self, key: str, mr_path: str):
        return True


@pytest.fixture
async def http_session():
    async with ClientSession() as session:
        yield session


async def test_auth_without_gitlab_token(
    localhost,
    aiomisc_unused_port_factory,
    http_session
):
    port = aiomisc_unused_port_factory()
    service = HttpService(
        address=localhost,
        port=port,
        st_client=StClientMock(
            url=URL('https://example.com'),
            session=http_session,
            token='secret',
            link_origin='example'
        ),
        gitlab_tokens=frozenset()
    )
    await service.start()

    url = URL.build(
        scheme='http', host=localhost, port=port, path='/gitlab'
    )
    async with http_session.post(url, json={}) as resp:
        assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('headers,expected_status', [
    ({}, HTTPStatus.UNAUTHORIZED),
    ({GITLAB_TOKEN_HEADER: 'token1'}, HTTPStatus.BAD_REQUEST),
    ({GITLAB_TOKEN_HEADER: 'token2'}, HTTPStatus.BAD_REQUEST)
])
async def test_auth_with_gitlab_token(
    localhost,
    aiomisc_unused_port_factory,
    http_session,
    headers,
    expected_status
):
    port = aiomisc_unused_port_factory()
    service = HttpService(
        address=localhost,
        port=port,
        st_client=StClientMock(
            url=URL('https://example.com'),
            session=http_session,
            token='secret',
            link_origin='example'
        ),
        gitlab_tokens=frozenset(['token1', 'token2'])
    )
    await service.start()

    url = URL.build(
        scheme='http', host=localhost, port=port, path='/gitlab'
    )
    async with http_session.post(url, headers=headers, json={}) as resp:
        assert resp.status == expected_status

