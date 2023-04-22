from typing import List

from aiomisc import entrypoint, Service
from aiomisc.service.raven import RavenSender
from aiomisc_log import basic_config

from yatracker_gitlab_linker.args import Parser
from yatracker_gitlab_linker.deps import config_deps
from yatracker_gitlab_linker.service import HttpService


def main():
    parser = Parser(
        auto_env_var_prefix='YATRACKER_GITLAB_LINKER_',
        config_files=[
            '.yatracker-gitlab-linker.ini',
            '~/.yatracker-gitlab-linker.ini',
            '/etc/yatracker-gitlab-linker.ini'
        ],
    )
    parser.parse_args()
    basic_config(level=parser.log_level, log_format=parser.log_format)

    config_deps(parser)

    services: List[Service] = [
        HttpService(address=parser.address, port=parser.port)
    ]

    if parser.sentry.dsn:
        services.append(
            RavenSender(
                sentry_dsn=parser.sentry.dsn,
                client_options={'environment': parser.sentry.env}
            )
        )

    with entrypoint(
        *services,
        log_level=parser.log_level,
        log_format=parser.log_format
    ) as loop:
        loop.run_forever()


if __name__ == '__main__':
    main()
