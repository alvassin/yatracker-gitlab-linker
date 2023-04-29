from aiohttp.web import Application, View

from yatracker_linker.st_client import StClient


class BaseView(View):
    URL_PATH = '/gitlab'

    @property
    def app(self) -> Application:
        return self.request.app

    @property
    def gitlab_tokens(self) -> frozenset[str]:
        return self.request.app['gitlab_tokens']

    @property
    def st_client(self) -> StClient:
        return self.request.app['st_client']
