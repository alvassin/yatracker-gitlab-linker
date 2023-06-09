from typing import Mapping

from aiohttp import ClientSession
from yarl import URL


class GitlabClient:
    def __init__(self, session: ClientSession, url: URL, token: str):
        self._session = session
        self._headers = {'Authorization': f'Bearer {token}'}
        self._base_url = url

    def get_url(self, url_path: str) -> str:
        # Concatenate URL as string to prevent re-encoding
        return f'{self._base_url}/api/v4/{url_path.lstrip("/")}'

    async def get_merge_request(
        self,
        project_id: str,
        merge_request_id: str
    ) -> Mapping:
        url = self.get_url(
            f'projects/{project_id}/merge_requests/{merge_request_id}'
        )
        async with self._session.get(url, headers=self._headers) as resp:
            return await resp.json()
