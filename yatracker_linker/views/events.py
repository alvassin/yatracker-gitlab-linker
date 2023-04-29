import asyncio
import logging
import re
from http import HTTPStatus
from typing import Any, List, Mapping, Literal

from aiohttp.web import HTTPBadRequest, HTTPUnauthorized, Response
from pydantic import BaseModel

from yatracker_linker.views.base import BaseView


PATTERN = re.compile(r'(?P<ticket>[a-z0-9]+-[0-9]+)', flags=re.IGNORECASE)
GITLAB_TOKEN_HEADER = 'X-Gitlab-Token'

log = logging.getLogger(__name__)


def get_ticket_candidates(*items: str) -> List[str]:
    candidates = set()
    for item in items:
        if matches := PATTERN.findall(item):
            candidates.update(matches)

    return list(sorted(candidate.upper() for candidate in candidates))


def get_mr_url_path(url, project_path_with_namespace):
    index = url.find(project_path_with_namespace)
    return url[index:]


class LastCommitModel(BaseModel):
    title: str
    message: str


class ObjectAttributesModel(BaseModel):
    url: str
    source_branch: str
    target_branch: str
    title: str
    description: str
    last_commit: LastCommitModel


class ProjectModel(BaseModel):
    path_with_namespace: str


class MergeRequestEventModel(BaseModel):
    event_type: Literal['merge_request']
    object_attributes: ObjectAttributesModel
    project: ProjectModel


class GitlabView(BaseView):
    URL_PATH = '/gitlab'

    async def get_tickets(self, event: MergeRequestEventModel) -> List[str]:
        candidates = get_ticket_candidates(
            event.object_attributes.last_commit.title,
            event.object_attributes.last_commit.message,
            event.object_attributes.source_branch,
            event.object_attributes.target_branch,
            event.object_attributes.title,
            event.object_attributes.description
        )

        log.debug('Get tickets for candidates %r', candidates)
        existing = await asyncio.gather(*[
            self.st_client.issue_exists(candidate)
            for candidate in candidates
        ])
        log.debug('Got existing tickets %r', existing)

        return [
            candidate
            for candidate, exists in zip(candidates, existing)
            if exists
        ]

    def assert_authorized(self):
        if self.gitlab_tokens:
            token = self.request.headers.get(GITLAB_TOKEN_HEADER)
            if token not in self.gitlab_tokens:
                raise HTTPUnauthorized

    async def post(self):
        try:
            self.assert_authorized()

            event_data = await self.request.json()
            log.debug('Received event %r', event_data)

            try:
                event = MergeRequestEventModel.parse_obj(event_data)
            except Exception:
                raise HTTPBadRequest

            mr_path = get_mr_url_path(
                event.object_attributes.url,
                event.project.path_with_namespace
            )
            if not mr_path:
                raise HTTPBadRequest(text='Unable to get merge request path')

            tickets = await self.get_tickets(event)
            if not tickets:
                log.info('No tickets to link with mr %s', mr_path)
                return Response(status=HTTPStatus.NO_CONTENT)

            log.info('Linking mr %s with tickets %r', mr_path, tickets)
            await asyncio.gather(*[
                self.st_client.link_issue(ticket, mr_path)
                for ticket in tickets
            ])

            return Response()
        except Exception as e:
            print(e)
            raise