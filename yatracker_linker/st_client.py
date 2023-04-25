from http import HTTPStatus

from aiohttp import ClientSession
from yarl import URL


class StClient:
    def __init__(
        self,
        session: ClientSession,
        url: URL,
        token: str,
        link_origin: str
    ):
        self._session = session
        self._headers = {'Authorization': f'OAuth {token}'}
        self._base_url = url
        self._link_origin = link_origin

    def get_url(self, url_path: str) -> URL:
        return self._base_url / url_path.lstrip('/')

    async def issue_exists(self, key: str):
        url = self.get_url(f'v2/issues/{key}')
        async with self._session.head(url, headers=self._headers) as resp:
            return resp.status == HTTPStatus.OK

    async def link_issue(self, key: str, mr_path: str):
        url = self.get_url(f'v2/issues/{key}/remotelinks')
        json = {
            'origin': self._link_origin,
            'relationship': 'relates',
            'key': mr_path
        }
        async with self._session.post(
            url, headers=self._headers, json=json
        ) as resp:
            return resp.ok
