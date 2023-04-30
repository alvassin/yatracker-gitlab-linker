from aiohttp import web
from aiomisc.service.aiohttp import AIOHTTPService

from yatracker_linker.tracker_client import TrackerClient
from yatracker_linker.views.events import GitlabView


class HttpService(AIOHTTPService):
    __dependencies__ = ('st_client',)
    __required__ = ('gitlab_tokens', )

    gitlab_tokens: frozenset[str]
    st_client: TrackerClient

    async def create_application(self):
        app = web.Application()
        app.router.add_route('POST', GitlabView.URL_PATH, GitlabView)

        app['gitlab_tokens'] = self.gitlab_tokens
        app['st_client'] = self.st_client

        return app
