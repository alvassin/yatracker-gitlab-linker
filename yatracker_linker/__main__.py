from typing import List

from aiomisc import Service, entrypoint
from aiomisc.service.raven import RavenSender
from aiomisc_log import basic_config

from yatracker_linker.args import Parser
from yatracker_linker.deps import config_deps
from yatracker_linker.service import HttpService


def main():
    parser = Parser(
        auto_env_var_prefix='YATRACKER_LINKER_',
        config_files=[
            '.yatracker-linker.ini',
            '~/.yatracker-linker.ini',
            '/etc/yatracker-linker.ini'
        ],
    )
    parser.parse_args()
    basic_config(level=parser.log_level, log_format=parser.log_format)

    config_deps(parser)

    services: List[Service] = [
        HttpService(
            address=parser.address,
            port=parser.port,
            gitlab_tokens=parser.gitlab.incoming_token
        )
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
