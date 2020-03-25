"""A collection of helper functions used for the main program
"""

from typing import Optional
from cameras import VirtCam
import os
import shutil
import sys
import cv2

from pathlib import Path

from pymba import Vimba, VimbaException, Frame


# todo add more colours
PIXEL_FORMATS_CONVERSIONS = {
    'BayerRG8': cv2.COLOR_BAYER_RG2RGB,
}


def display_frame(frame: Frame, delay: Optional[int] = 1) -> None:
    """
    Displays the acquired frame.
    :param frame: The frame object to display.
    :param delay: Display delay in milliseconds, use 0 for indefinite.
    """
    print('frame {}'.format(frame.data.frameID))

    # get a copy of the frame data
    image = frame.buffer_data_numpy()

    # convert colour space if desired
    try:
        image = cv2.cvtColor(image, PIXEL_FORMATS_CONVERSIONS[frame.pixel_format])
    except KeyError:
        pass

    # display image
    cv2.imshow('Image', image)
    cv2.waitKey(delay)


def get_frame(frames=1, cam=0):
    """Get a frame from a vimba camera

    Args:
        frames (int): The amount of frames to get.
            Defaults to 1
        cam: The index(int) or camera_id(str)
            Defaults to 0

    Returns:
        list of images

    Raises:
        Stuff
    """

    frames = []
    with Vimba() as vimba:
        camera = vimba.camera(cam)
        camera.open()

        camera.arm('SingleFrame')

        # capture a single frame, more than once if desired
        for i in range(frames):
            try:
                frames.append(camera.acquire_frame())
                display_frame(frames[i], 0)
            except VimbaException as e:
                # rearm camera upon frame timeout
                if e.error_code == VimbaException.ERR_TIMEOUT:
                    print(e)
                    camera.disarm()
                    camera.arm('SingleFrame')
                else:
                    raise

        camera.disarm()
        camera.close()
        return frames


def framediffs(camera: VirtCam, out_folder: Path, overwrite=False):
    """
    Create a series of frame differences between all subsequent frames of VirtCam.

    Args:
        camera: A virtual camera object
        out_dir: The directory to put output frames in
        overwrite: If the output directory should be removed if it exists on start

    Returns:
        nothing
    """

    if out_folder.is_dir():
        if overwrite:
            shutil.rmtree(out_folder)
        else:
            raise FileExistsError('Overwrite not specified')
    os.makedirs(out_folder)

    f = camera.get_frame()
    w, h, _ = f.shape

    background = cv2.cvtColor(camera.get_frame(), cv2.COLOR_BGR2GRAY)
    w, h = background.shape
    img_array = []

    while not camera.is_last_frame:
        frame = cv2.cvtColor(camera.get_frame(), cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(background, frame)
        _, binary = cv2.threshold(diff, 10, 255, cv2.THRESH_BINARY)
        img_array.append(binary)

    for i in range(len(img_array)):
        cv2.imwrite(os.path.join(out_folder, f'out{i}.png'), img_array[i])


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print('No args provided\n\tin_dir out_dir overwrite\n\timages_series1 output1 true')
        exit(1)

    in_dir = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    overwrite = False

    if len(sys.argv) > 3:
        overwrite = sys.argv[3].lower() == "true"

    camera = VirtCam(in_dir)
    print(camera.has_frames)
    framediffs(camera, out_dir, overwrite)
