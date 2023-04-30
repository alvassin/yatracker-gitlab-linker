import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from functools import partial
from typing import List, Literal

from aiohttp.web import HTTPBadRequest, HTTPUnauthorized, json_response
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
from pydantic.fields import Field

from yatracker_linker.views.base import BaseView


PATTERN = re.compile(r'(?P<ticket>[a-z0-9]+-[0-9]+)', flags=re.IGNORECASE)
GITLAB_TOKEN_HEADER = 'X-Gitlab-Token'

log = logging.getLogger(__name__)


@dataclass
class LinkItem:
    path: str
    issue: str


def convert(obj):
    if isinstance(obj, LinkItem):
        return asdict(obj)

    raise ValueError(f'Fail to convert object {obj}')


json_dumps = partial(json.dumps, default=convert)


def get_ticket_candidates(*items: str) -> List[str]:
    candidates = set()
    for item in items:
        if matches := PATTERN.findall(item):
            candidates.update(matches)

    return list(sorted(candidate.upper() for candidate in candidates))


class CommitModel(BaseModel):
    title: str
    message: str
    url: str


class ObjectAttributesModel(BaseModel):
    url: str
    source_branch: str
    target_branch: str
    title: str
    description: str
    last_commit: CommitModel


class ProjectModel(BaseModel):
    path_with_namespace: str


class MergeRequestEventModel(BaseModel):
    object_kind: Literal['merge_request']
    object_attributes: ObjectAttributesModel
    project: ProjectModel

    def get_items_to_link(self) -> List[LinkItem]:
        issues = get_ticket_candidates(
            self.object_attributes.last_commit.title,
            self.object_attributes.last_commit.message,
            self.object_attributes.source_branch,
            self.object_attributes.target_branch,
            self.object_attributes.title,
            self.object_attributes.description
        )

        merge_request_path = get_relative_url_path(
            self.object_attributes.url,
            self.project.path_with_namespace
        )

        log.debug(
            'Got candidates to link with MR %s: %r',
            self.object_attributes.url, issues
        )

        return [
            LinkItem(issue=issue, path=merge_request_path)
            for issue in issues
        ]


class PushEventModel(BaseModel):
    object_kind: Literal['push']
    project: ProjectModel
    commits: List[CommitModel]

    def get_items_to_link(self) -> List[LinkItem]:
        items_to_link = []
        for commit in self.commits:
            if issues := get_ticket_candidates(commit.title, commit.message):
                commit_path = get_relative_url_path(
                    commit.url, self.project.path_with_namespace
                )
                for issue in issues:
                    items_to_link.append(
                        LinkItem(path=commit_path, issue=issue)
                    )

                log.debug(
                    'Got candidates to link with commit %s: %r',
                    commit_path, issues
                )

        return items_to_link


class EventModel(BaseModel):
    event: PushEventModel | MergeRequestEventModel = Field(
        ..., discriminator='object_kind'
    )


def get_relative_url_path(url, project_path_with_namespace):
    index = url.find(project_path_with_namespace)
    return url[index:]


class GitlabView(BaseView):
    URL_PATH = '/gitlab'

    def assert_authorized(self):
        if self.gitlab_tokens:
            token = self.request.headers.get(GITLAB_TOKEN_HEADER)
            if token not in self.gitlab_tokens:
                raise HTTPUnauthorized

    async def get_event(self) -> PushEventModel | MergeRequestEventModel:
        try:
            data = await self.request.json()
            log.debug('Received event %r', data)
            return EventModel(event=data).event
        except ValidationError:
            raise HTTPBadRequest(text='Unknown object kind')

    async def post(self):
        try:
            self.assert_authorized()

            event = await self.get_event()
            items_to_link = event.get_items_to_link()

            linked_items = []
            if items_to_link:
                link_results = await asyncio.gather(*[
                    self.st_client.link_issue(item.issue, item.path)
                    for item in items_to_link
                ])
                linked_items = [
                    item
                    for item, linked in zip(items_to_link, link_results)
                    if linked
                ]

            log.info('Linked items: %r', linked_items)
            return json_response(linked_items, dumps=json_dumps)
        except Exception as e:
            print(e)
            raise
