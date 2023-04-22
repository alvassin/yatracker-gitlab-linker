from aiohttp import web
from aiomisc.service.aiohttp import AIOHTTPService

from yatracker_gitlab_linker.st_client import StClient
from yatracker_gitlab_linker.views.event import EventView


class HttpService(AIOHTTPService):
    __dependencies__ = (
        'st_client',
    )

    st_client: StClient

    async def create_application(self):
        app = web.Application()
        app.router.add_route('GET', EventView.URL_PATH, EventView)

        app['st_client'] = self.st_client

        return app
