#!/usr/bin/env python3
from time import sleep

from milc import cli

from defector.argument_types import dir_path
from defector.communication import set_speed


@cli.argument('-i', '--input', type=dir_path, help='Directory containing the image sequence. Has to end in a number sequence')
@cli.subcommand("Hello world command")
def hello(cli):
    cli.log.info('Hello there!')

    if cli.config.hello.input:
        cli.log.info(f'path is {cli.config.hello.input.resolve()}')


@cli.argument('-d', '--decel', type=int, help="help", default=125)
@cli.argument('-a', '--accel', type=int, help="help", default=125)
@cli.argument('-s', '--speed', type=int, help="Speed to spin the vial at 0-1000", default=200)
@cli.subcommand("Test stuff")
def test(cli):
    set_speed(cli.config.test.speed, cli.config.test.accel, cli.config.test.decel)
    sleep(10)
    set_speed(0, cli.config.test.accel, cli.config.test.decel)
