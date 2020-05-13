import shutil
import os
from pathlib import Path
from time import sleep

import cv2
from milc import cli

from defector.argument_types import dir_path
from defector.helpers import roi_crop, get_folder, blob_detection, find_contours, correct_ambient, make_hist


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
            while cli.config.framediff.output.is_dir():
                pass
            sleep(0.5)
        else:
            cli.log.error(f'{str(cli.config.framediff.output)} already exists, and overwrite isn\'t forced')
            return False
    os.makedirs(cli.config.framediff.output)

    images = get_folder(cli.config.framediff.input.resolve())

    size = None
    for idx, img in enumerate(images[:-cli.config.framediff.distance]):
        background = cv2.imread(img, cv2.IMREAD_COLOR)
        frame = cv2.imread(images[idx + cli.config.framediff.distance], cv2.IMREAD_COLOR)

        if cli.config.framediff.roi:
            size, background = roi_crop(background, size)
            _, frame = roi_crop(frame, size)

        # _, binary = cv2.threshold(background, 120, 255, cv2.THRESH_BINARY)
        # blobbed = blob_detection(binary)

        contours, center_img = find_contours(background)

        cv2.imwrite(str(cli.config.framediff.output.joinpath(f'out{idx}.png')), center_img)
