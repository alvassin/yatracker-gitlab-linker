from aiohttp.web import Application, View

from yatracker_linker.gitlab_client import GitlabClient
from yatracker_linker.tracker_client import TrackerClient


class BaseView(View):
    URL_PATH = '/gitlab'

    @property
    def app(self) -> Application:
        return self.request.app

    @property
    def gitlab_tokens(self) -> frozenset[str]:
        return self.request.app['gitlab_tokens']

    @property
    def st_client(self) -> TrackerClient:
        return self.request.app['st_client']

    @property
    def gitlab_client(self) -> GitlabClient:
        return self.request.app['gitlab_client']

    @property
    def gitlab_favicon(self) -> str:
        return self.request.app['gitlab_favicon']
