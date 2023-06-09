from typing import Optional

import argclass
from aiomisc_log import LogFormat
from yarl import URL


class SentryGroup(argclass.Group):
    dsn: Optional[URL]
    env: Optional[str]


class TrackerGroup(argclass.Group):
    url: URL
    token: str
    link_origin: str


class GitlabGroup(argclass.Group):
    url: URL
    incoming_token: frozenset[str] = argclass.Argument(
        type=str, nargs='*', converter=frozenset, help=(
            'Tokens used by gitlab to authenticate at linker using '
            'X-Gitlab-Token header'
        )
    )
    outgoing_token: str = argclass.Argument(type=str, help=(
        'Token used by linker to authenticate at gitlab to retrieve merge '
        'requests information'
    ))


class Parser(argclass.Parser):
    log_level: int = argclass.LogLevel
    log_format: str = argclass.Argument(
        choices=LogFormat.choices(),
        default=LogFormat.default()
    )
    address: str = argclass.Argument(default='0.0.0.0')
    port: int

    gitlab = GitlabGroup(title='Gitlab options')
    sentry = SentryGroup(title='Sentry options')
    tracker = TrackerGroup(title='Tracker options')
