from contextlib import asynccontextmanager
from copy import deepcopy
from http import HTTPStatus
from typing import Iterable, Optional
from unittest.mock import patch

import pytest
from aiohttp import ClientSession, hdrs
from aiohttp.test_utils import TestServer
from aiohttp.web import Application, Request, Response, middleware
from yarl import URL

from yatracker_linker.service import HttpService
from yatracker_linker.tracker_client import TrackerClient
from yatracker_linker.views.events import GITLAB_TOKEN_HEADER


TRACKER_SECRET = 'tracker-secret'
TRACKER_LINK_ORIGIN = 'example.origin'
MR_PATH = 'alvassin/example/-/merge_requests/1'
COMMIT_PATH = (
    'alvassin/example/-/commit/c5feabde2d8cd023215af4d2ceeb7a64839fc428'
)

# Contains only required fields by yatracker-linker
MR_EVENT_SAMPLE = {
    'object_kind': 'merge_request',
    'project': {'path_with_namespace': 'alvassin/example'},
    'object_attributes': {
        'description': '',
        'source_branch': 'EXAMPLETASK-123',
        'target_branch': 'master',
        'title': 'Update README.md',
        'url': f'http://gitlab.local/{MR_PATH}',
        'last_commit': {
            'message': 'Update README.md',
            'title': 'Update README.md',
            'url': f'http://gitlab.local/{COMMIT_PATH}',
        }
    }
}

PUSH_EVENT_SAMPLE = {
    'object_kind': 'push',
    'project': {'path_with_namespace': 'alvassin/example'},
    'commits': [{
        'message': 'RESP-200',
        'title': 'Example commit',
        'url': f'http://gitlan.local/{COMMIT_PATH}',
    }]
}


@pytest.fixture
async def st_server(aiomisc_unused_port_factory):
    async def handler(request: Request):
        return Response(status=int(request.match_info['id']))

    @middleware
    async def track_middleware(request: Request, handler):
        request.app['requests'].append({
            'url': request.url,
            'headers': request.headers,
            'json': await request.json()
        })
        return await handler(request)

    app = Application(middlewares=[track_middleware])
    app['requests'] = []
    app.router.add_route(
        'post', '/v2/issues/RESP-{id:\\d+}/remotelinks', handler
    )

    server = TestServer(app, port=aiomisc_unused_port_factory())
    await server.start_server()

    try:
        yield server
    finally:
        await server.close()


@pytest.fixture
def st_server_url(st_server):
    return st_server.make_url('/')


@pytest.fixture
async def http_session():
    async with ClientSession() as session:
        yield session


@pytest.fixture
def st_client(http_session, st_server_url):
    return TrackerClient(
        url=st_server_url,
        session=http_session,
        token=TRACKER_SECRET,
        link_origin=TRACKER_LINK_ORIGIN
    )


@pytest.fixture
def http_service_port(aiomisc_unused_port_factory):
    return aiomisc_unused_port_factory()


@pytest.fixture
def http_service_url(localhost, http_service_port):
    return URL.build(
        scheme='http', host=localhost, port=http_service_port, path='/gitlab'
    )


@pytest.fixture
def http_service_factory(localhost, http_service_port, st_client):
    @asynccontextmanager
    async def factory(tokens: Optional[Iterable[str]] = None):
        service = HttpService(
            address=localhost,
            port=http_service_port,
            st_client=st_client,
            gitlab_tokens=frozenset(tokens or [])
        )
        await service.start()
        yield
        await service.stop()
    return factory


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
        {GITLAB_TOKEN_HEADER: 'invalid'},
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
    expected_status,
    st_client
):
    async with http_service_factory(tokens=gitlab_tokens):
        # We don't want make too many requests here
        with patch.object(st_client, 'link_issue', return_value=True):
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
    async with http_service_factory():
        async with http_session.post(http_service_url, json={}) as resp:
            assert resp.status == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize('issue,expected_response', [
    # For successful response we expect one linked issue
    ('RESP-200', [{'issue': 'RESP-200', 'path': MR_PATH}]),

    # For failed responses we expect no linked issues
    ('RESP-401', []),
    ('RESP-500', []),
])
async def test_link_merge_request_with_tracker(
    http_session,
    http_service_factory,
    http_service_url,
    st_server,
    issue,
    expected_response
):
    async with http_service_factory():
        event = deepcopy(MR_EVENT_SAMPLE)
        event['object_attributes']['source_branch'] = issue
        async with http_session.post(http_service_url, json=event) as resp:
            # yatracker-linker response always should be ok
            assert resp.status == HTTPStatus.OK
            resp_content = await resp.json()

    assert resp_content == expected_response

    # Check correct number of tracker requests was performed
    assert len(st_server.app['requests']) == 1
    request = st_server.app['requests'][0]

    # Check correct URL was called
    assert request['url'].path == f'/v2/issues/{issue}/remotelinks'

    # Check tracker received auth headers
    assert request['headers'].get(hdrs.AUTHORIZATION) == (
        f'OAuth {TRACKER_SECRET}'
    )

    # Check data received by Tracker
    assert request['json'] == {
        'origin': TRACKER_LINK_ORIGIN,
        'relationship': 'relates',
        'key': MR_PATH
    }


async def test_link_commits_with_tracker(
    http_session,
    http_service_factory,
    http_service_url,
    st_server
):
    async with http_service_factory():
        async with http_session.post(
            http_service_url, json=PUSH_EVENT_SAMPLE
        ) as resp:
            assert resp.status == HTTPStatus.OK
            resp_content = await resp.json()

    assert resp_content == [{'issue': 'RESP-200', 'path': COMMIT_PATH}]

    # Check correct number of tracker requests was performed
    assert len(st_server.app['requests']) == 1
    request = st_server.app['requests'][0]

    # Check correct URL was called
    assert request['url'].path == f'/v2/issues/RESP-200/remotelinks'

    # Check tracker received auth headers
    assert request['headers'].get(hdrs.AUTHORIZATION) == (
        f'OAuth {TRACKER_SECRET}'
    )

    # Check data received by Tracker
    assert request['json'] == {
        'origin': TRACKER_LINK_ORIGIN,
        'relationship': 'relates',
        'key': COMMIT_PATH
    }
