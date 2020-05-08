from pathlib import Path

from milc import cli

from defector.cameras import PymbaCam


@cli.argument('-n', '--img_count', type=int, help="Number of images to capture.", default=100)
@cli.argument('-f', '--force', help='Remove output directory if it exists. !!THIS REMOVES THE ENTIRE DIRECTORY!!', action='store_true')
@cli.argument('-o', '--output', type=Path, help='Output directory to save images sequence in', default='framediff_output', required=True)
@cli.subcommand('Capture a sequence of images and save them')
def capture(cli):
    cam = PymbaCam()

    cam.capture(cli.config.capture.img_count)
    cam.save_images(cli.config.capture.output, cli.config.capture.force)
