import shutil
import os
from pathlib import Path

import cv2
from milc import cli

from defector.argument_types import dir_path
from defector.helpers import roi_crop, get_folder


@cli.argument('-d', '--distance', help='The distance in frames to diff over', type=int, default=1)
@cli.argument('-r', '--roi', help='Crop ROI of all images', action='store_false')
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

    images = get_folder(cli.config.framediff.input.resolve())

    for idx, img in enumerate(images[:-cli.config.framediff.distance]):
        background = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
        frame = cv2.imread(images[idx + cli.config.framediff.distance], cv2.IMREAD_GRAYSCALE)

        if cli.config.framediff.roi:
            background = roi_crop(background)
            frame = roi_crop(frame)

        diff = cv2.absdiff(background, frame)
        _, binary = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)
        cv2.imwrite(str(cli.config.framediff.output.joinpath(f'out{idx}.png')), binary)
