from typing import Mapping, Optional

from aiohttp import ClientSession, hdrs
from yarl import URL


class GitlabClient:
    def __init__(self, session: ClientSession, url: URL, token: str):
        self._session = session
        self._headers = {'Authorization': f'Bearer {token}'}
        self._base_url = url

    async def get_favicon(self) -> Optional[str]:
        url = f'{self._base_url}/favicon.ico'
        async with self._session.get(
            url,
            headers=self._headers,
            allow_redirects=False
        ) as resp:
            return resp.headers.get(hdrs.LOCATION)

    async def get_merge_request(
        self,
        project_id: str,
        merge_request_id: str
    ) -> Mapping:
        url = (
            f'{self._base_url}/api/v4/'
            f'projects/{project_id}/merge_requests/{merge_request_id}'
        )
        async with self._session.get(url, headers=self._headers) as resp:
            return await resp.json()
