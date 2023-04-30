from aiohttp import ClientSession
from yarl import URL


class TrackerClient:
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

    async def link_issue(self, key: str, remote_path: str):
        url = self.get_url(f'v2/issues/{key}/remotelinks')
        json = {
            'origin': self._link_origin,
            'relationship': 'relates',
            'key': remote_path
        }
        async with self._session.post(
            url, headers=self._headers, json=json
        ) as resp:
            return resp.ok
