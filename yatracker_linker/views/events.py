import asyncio
import logging
import re
from typing import List, Literal

from aiohttp.web import HTTPBadRequest, HTTPUnauthorized, json_response
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

    def get_merge_request_path(self) -> str:
        index = self.object_attributes.url.find(
            self.project.path_with_namespace
        )
        return self.object_attributes.url[index:]


class GitlabView(BaseView):
    URL_PATH = '/gitlab'

    def assert_authorized(self):
        if self.gitlab_tokens:
            token = self.request.headers.get(GITLAB_TOKEN_HEADER)
            if token not in self.gitlab_tokens:
                raise HTTPUnauthorized

    async def link_issues(
        self,
        event: MergeRequestEventModel,
        merge_request_path: str
    ) -> List[str]:
        issues = get_ticket_candidates(
            event.object_attributes.last_commit.title,
            event.object_attributes.last_commit.message,
            event.object_attributes.source_branch,
            event.object_attributes.target_branch,
            event.object_attributes.title,
            event.object_attributes.description
        )
        log.debug(
            'Got candidates to link with MR %s: %r',
            event.object_attributes.url, issues
        )

        if not issues:
            return []

        link_results = await asyncio.gather(*[
            self.st_client.link_issue(issue, merge_request_path)
            for issue in issues
        ])

        return [
            issue
            for issue, linked in zip(issues, link_results)
            if linked
        ]

    async def get_event(self) -> MergeRequestEventModel:
        try:
            data = await self.request.json()
            log.debug('Received event %r', data)
            return MergeRequestEventModel.parse_obj(data)
        except Exception:
            raise HTTPBadRequest

    async def post(self):
        self.assert_authorized()

        event = await self.get_event()

        mr_path = event.get_merge_request_path()
        if not mr_path:
            raise HTTPBadRequest(text='Unable to get merge request path')

        linked_issues = await self.link_issues(event, mr_path)
        log.info('Linked mr %s with tickets: %r', mr_path, linked_issues)

        return json_response({
            'linked_issues': linked_issues,
            'merge_request_path': mr_path
        })
