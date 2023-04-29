from contextlib import ExitStack
from http import HTTPStatus
from typing import Iterable, Optional
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from yarl import URL

from yatracker_linker.service import HttpService
from yatracker_linker.st_client import StClient
from yatracker_linker.views.events import GITLAB_TOKEN_HEADER


# Contains only required fields by yatracker-linker
MR_EVENT_SAMPLE = {
  "event_type": "merge_request",
  "project": {"path_with_namespace": "alvassin/example"},
  "object_attributes": {
    "description": "",
    "source_branch": "EXAMPLETASK-123",
    "target_branch": "master",
    "title": "Update README.md",
    "url": "http://gitlab.local/alvassin/example/-/merge_requests/1",
    "last_commit": {
      "message": "Update README.md",
      "title": "Update README.md",
      "url": (
          "http://gitlab.local/alvassin/example/-/"
          "commit/6800a5742f4793c4335a357ae11bdef01c9d5668"
      ),
    }
  }
}


@pytest.fixture
async def http_session():
    async with ClientSession() as session:
        yield session


@pytest.fixture
def mocked_st_client(http_session):
    client = StClient(
        url=URL('http://example.com'),
        session=http_session,
        token='secret',
        link_origin='example.origin'
    )

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(client, 'issue_exists', return_value=True)
        )
        stack.enter_context(
            patch.object(client, 'link_issue', return_value=True)
        )
        yield client


@pytest.fixture
def http_service_factory(
    localhost,
    aiomisc_unused_port,
    http_session,
    mocked_st_client
):
    def factory(tokens: Optional[Iterable[str]] = None):
        return HttpService(
            address=localhost,
            port=aiomisc_unused_port,
            st_client=mocked_st_client,
            gitlab_tokens=frozenset(tokens or [])
        )
    return factory


@pytest.fixture
def http_service_url(localhost, aiomisc_unused_port):
    return URL.build(
        scheme='http',
        host=localhost,
        port=aiomisc_unused_port,
        path='/gitlab'
    )


@pytest.mark.parametrize('gitlab_tokens,headers,expected_status', [
    # Service started without specified gitlab tokens, access is allowed
    # without any headers
    (frozenset(), {}, HTTPStatus.OK),

    # Service started with specified gitlab tokens, no header provided,
    # access denied
    (frozenset(['token1', 'token2']), {}, HTTPStatus.UNAUTHORIZED),

    # Service started with specified gitlab tokens, bad header provided,
    # access denied
    (
        frozenset(['token1', 'token2']),
        {GITLAB_TOKEN_HEADER: 'inavlid'},
        HTTPStatus.UNAUTHORIZED
    ),

    # Service started with specified gitlab tokens, correct header provided,
    # access allowed
    (
        frozenset(['token1', 'token2']),
        {GITLAB_TOKEN_HEADER: 'token1'},
        HTTPStatus.OK
    ),
    (
        frozenset(['token1', 'token2']),
        {GITLAB_TOKEN_HEADER: 'token2'},
        HTTPStatus.OK
    )
])
async def test_service_with_gitlab_tokens_auth(
    http_session,
    http_service_factory,
    http_service_url,
    gitlab_tokens,
    headers,
    expected_status
):
    service = http_service_factory(tokens=gitlab_tokens)
    await service.start()

    async with http_session.post(
        http_service_url,
        headers=headers,
        json=MR_EVENT_SAMPLE
    ) as resp:
        assert resp.status == expected_status


async def test_invalid_event_data(
    http_session,
    http_service_factory,
    http_service_url,
):
    service = http_service_factory()
    await service.start()

    async with http_session.post(http_service_url, json={}) as resp:
        assert resp.status == HTTPStatus.BAD_REQUEST
