import logging
from http import HTTPStatus
from urllib.parse import quote_plus

from aiohttp.client_exceptions import ClientResponseError
from aiohttp.web import HTTPNotFound, json_response

from yatracker_linker.views.base import BaseView


log = logging.getLogger(__name__)


class ProxyView(BaseView):
    URL_PATH = r'/{project_id:.*}/-/merge_requests/{merge_request_id:\d+}'

    async def get(self):
        project_id = self.request.match_info['project_id']
        merge_request_id = self.request.match_info['merge_request_id']

        try:
            merge_request = await self.gitlab_client.get_merge_request(
                project_id=quote_plus(project_id),
                merge_request_id=merge_request_id,
            )
        except ClientResponseError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                raise HTTPNotFound()

            log.exception(
                'Unable to get merge request %r in project_id %r',
                project_id, merge_request_id
            )
            raise

        # self.request.url.path
        # self.gitlab_client.get_merge_request()
        # GET /projects/:id/merge_requests/:merge_request_iid
        return json_response({
            'key': self.request.url.path,
            'summary': merge_request['title'],
            'assignee': {
                'login': merge_request['author']['username']
            },
            'updated': merge_request['updated_at'],
            'resolution': {
                'name': (
                    'unresolved'
                    if merge_request['state'] not in ('merged', 'closed')
                    else 'resolved'
                ),
            },
            # opened, closed, merged or locked
            'status': {
                'name': merge_request['state']
            }
        })
