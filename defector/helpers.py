"""A collection of helper functions used for the main program
"""

from typing import Optional
from cameras import VirtCam
import os
import shutil
import cv2

from pymba import Vimba, VimbaException, Frame


def twice(x):
    """A basic example function used to show off pytest"""

    return x * 2


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


def framediffs(camera: VirtCam):
    """
    Create a series of frame differences between all subsequent frames of VirtCam.

    Args:
        image_path (string) the path to folder with images

    Returns:
        static_bg (np.array): The extracted static background
    """
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

    out_folder = os.path.join(camera.image_path, 'frame_differences')
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)
    os.makedirs(out_folder)

    for i in range(len(img_array)):
        cv2.imwrite(os.path.join(out_folder, f'out{i}.png'), img_array[i])


if __name__ == "__main__":
    camera = VirtCam(os.path.join(os.path.dirname(__file__), '../project-bin/vimba_image_series/dust'))
    print(camera.has_frames)
    framediffs(camera)
