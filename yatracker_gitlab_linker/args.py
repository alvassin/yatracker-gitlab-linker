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


class Parser(argclass.Parser):
    log_level: int = argclass.LogLevel
    log_format: str = argclass.Argument(
        choices=LogFormat.choices(),
        default=LogFormat.default()
    )
    address: str = argclass.Argument(default='0.0.0.0')
    port: int

    sentry = SentryGroup(title='Sentry options')
    tracker = TrackerGroup(title='Tracker options')
