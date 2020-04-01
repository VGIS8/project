import shutil
import os
from pathlib import Path

import cv2
from milc import cli

from defector.cameras import VirtCam
from defector.argument_types import dir_path


@cli.argument('-f', '--force', help='Remove output directory if it exists. !!THIS REMOVES THE ENTIRE DIRECTORY!!', action='store_true')
@cli.argument('-i', '--input', type=dir_path, help='Directory containing the image sequence. Has to end in a number sequence', required=True)
@cli.argument('-o', '--output', type=Path, help='Output directory to save images sequence in', default='framediff_output')
@cli.subcommand("Generates sequence of frame differences from input image sequence")
def framediff(cli):
    """
    Create a series of frame differences between all subsequent frames of VirtCam.
    """

    if cli.config.framediff.output.is_dir():
        if cli.config.framediff.force:
            shutil.rmtree(cli.config.framediff.output)
        else:
            cli.log.error(f'{str(cli.config.framediff.output)} already exists, and overwrite isn\'t forced')
            return False
    os.makedirs(cli.config.framediff.output)

    camera = VirtCam(cli.config.framediff.input.resolve())

    f = camera.get_frame()
    w, h, _ = f.shape

    background = cv2.cvtColor(camera.get_frame(), cv2.COLOR_BGR2GRAY)
    w, h = background.shape
    img_array = []

    while not camera.is_last_frame:
        frame = cv2.cvtColor(camera.get_frame(), cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(background, frame)
        _, binary = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)
        img_array.append(binary)
        background = frame

    for idx, image in enumerate(img_array):
        cv2.imwrite(str(cli.config.framediff.output.joinpath(f'out{idx}.png')), img_array[idx])
