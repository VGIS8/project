#!/usr/bin/env python3

from milc import cli

from defector.argument_types import dir_path


@cli.argument('-i', '--input', type=dir_path, help='Directory containing the image sequence. Has to end in a number sequence')
@cli.subcommand("Hello world command")
def hello(cli):
    cli.log.info('Hello there!')

    if cli.config.hello.input:
        cli.log.info(f'path is {cli.config.hello.input.resolve()}')
