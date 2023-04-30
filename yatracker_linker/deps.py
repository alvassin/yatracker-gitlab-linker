from aiohttp import ClientSession
from aiomisc_dependency import dependency, reset_store

from yatracker_linker.args import Parser
from yatracker_linker.tracker_client import TrackerClient


async def st_client(parser: Parser):
    async with ClientSession() as session:
        yield TrackerClient(
            session=session,
            url=parser.tracker.url,
            token=parser.tracker.token,
            link_origin=parser.tracker.link_origin
        )


def config_deps(args):

    @dependency
    def parser() -> Parser:
        return args

    dependency(st_client)


def reset_deps():
    reset_store()
