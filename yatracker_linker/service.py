from aiohttp import web
from aiomisc.service.aiohttp import AIOHTTPService

from yatracker_linker.gitlab_client import GitlabClient
from yatracker_linker.tracker_client import TrackerClient
from yatracker_linker.views.events import GitlabView
from yatracker_linker.views.proxy import ProxyView


class HttpService(AIOHTTPService):
    __dependencies__ = (
        'st_client',
        'gitlab_client',
        'gitlab_favicon',
    )
    __required__ = ('gitlab_tokens', )

    gitlab_tokens: frozenset[str]
    st_client: TrackerClient
    gitlab_client: GitlabClient
    gitlab_favicon: str

    async def create_application(self):
        app = web.Application()
        app.router.add_route('POST', GitlabView.URL_PATH, GitlabView)
        app.router.add_route('GET', ProxyView.URL_PATH, ProxyView)

        app['gitlab_tokens'] = self.gitlab_tokens
        app['st_client'] = self.st_client
        app['gitlab_client'] = self.gitlab_client
        app['gitlab_favicon'] = self.gitlab_favicon

        return app
