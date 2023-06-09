from aiohttp import ClientSession
from aiomisc_dependency import dependency, reset_store

from yatracker_linker.args import Parser
from yatracker_linker.gitlab_client import GitlabClient
from yatracker_linker.tracker_client import TrackerClient


async def st_client(parser: Parser):
    async with ClientSession() as session:
        yield TrackerClient(
            session=session,
            url=parser.tracker.url,
            token=parser.tracker.token,
            link_origin=parser.tracker.link_origin
        )


async def gitlab_client(parser: Parser):
    async with ClientSession(raise_for_status=True) as session:
        yield GitlabClient(
            session=session,
            url=parser.gitlab.url,
            token=parser.gitlab.outgoing_token
        )


def config_deps(args):

    @dependency
    def parser() -> Parser:
        return args

    dependency(st_client)
    dependency(gitlab_client)


def reset_deps():
    reset_store()
