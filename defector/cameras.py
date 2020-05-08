"""Provides functions to get camera matrix and calibration vector
"""

from shutil import rmtree
import os
import glob
import re
from pathlib import Path
from time import sleep

import cv2 as cv
import numpy as np
from pymba import Vimba, Frame


def sort_key_func(s):
    """Return the first number you find in string. 0 if not"""
    nums = re.findall('[0-9]+', Path(s).name)
    if nums == []:
        return 0
    else:
        return int(nums[0])


class VirtCam:
    """Provides a camera compatible class, that instead streams images from a folder"""

    # termination criteria
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    checker_board_size = (9, 6)

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.
    camera_matrix = None
    distortion_vector = None
    images = None
    file_types = ['jpg', 'png']
    frame_cnt = 0
    has_frames = False
    is_last_frame = True
    image_path = ""

    def __init__(self, image_path, file_types=None, checker_board_size=None):
        if file_types is not None:
            self.file_types = file_types

        if checker_board_size is not None:
            self.checker_board_size = checker_board_size

        self.objpoints = np.zeros((self.checker_board_size[0] * self.checker_board_size[1], 3), np.float32)
        self.objpoints[:, :2] = np.mgrid[0:self.checker_board_size[0], 0:self.checker_board_size[1]].T.reshape(-1, 2)

        self.images = []
        for e in self.file_types:
            self.images.extend(glob.glob(f'{image_path}/*.{e}'))
        self.images.sort(key=sort_key_func)

        if self.images != []:
            self.has_frames = True
            self.is_last_frame = False
        self.image_path = image_path

    def get_frame(self):
        """Get the next frame in the sequence
        Args:

        Returns:
            frame (list): RGB values or []
        """

        if not self.has_frames:
            return None

        self.is_last_frame = False

        frame = self.images[self.frame_cnt]
        self.frame_cnt += 1

        if self.frame_cnt >= len(self.images):
            self.frame_cnt = 0
            self.is_last_frame = True

        print(frame)

        return cv.imread(frame)


class PymbaCam:

    vimba = Vimba()
    vimba.startup()
    camera = vimba.camera(0)

    PIXEL_FORMATS_CONVERSIONS = {
        'BayerRG8': cv.COLOR_BAYER_RG2RGB,
    }

    def __init__(self, mode='Continuous', cam_idx=0):
        self.camera = self.vimba.camera(cam_idx)

        self.is_last_frame = True
        self.img_buffer = []
        self.img_ID = 0
        if mode not in 'Continuous':  # SingleFrame']:
            raise NotImplementedError(f"{mode} is not a valid mode or not implemented. Use Continuous")

        self.camera.open()
        self.camera.arm('Continuous', self.continous_cb)

    def __del__(self):
        # stop frame acquisition
        # start_frame_acquisition can simply be called again if the camera is still armed
        self.camera.stop_frame_acquisition()
        self.camera.disarm()
        self.camera.close()

    def continous_cb(self, frame: Frame):
        """Callback for receiving frames when they're ready

        Args:
            frame: The frame object

        """

        self.img_ID = frame.data.frameID

        # If the frame is incomplte, discard it (VmbFrame_t.receiveStatus does not equal VmbFrameStatusComplete)
        if frame.data.receiveStatus == -1:
            return

        # get a copy of the frame data
        try:
            image = frame.buffer_data_numpy()
        except NotImplementedError as err:
            print(f'noe{err}')
            return

        # convert colour space if desired
        try:
            image = cv.cvtColor(image, self.PIXEL_FORMATS_CONVERSIONS[frame.pixel_format])
        except KeyError:
            pass

        self.img_buffer.append(image)

    def capture(self, num_of_images=100):
        self.img_buffer = []
        self.camera.start_frame_acquisition()

        # stream images for a while...
        while len(self.img_buffer) < num_of_images:
            sleep(0.001)

        self.camera.stop_frame_acquisition()

        print(len(self.img_buffer))
        print(self.img_ID)

    def save_images(self, dir, overwrite=False):
        """Save the image buffer to a folder of frames

        Args:
            dir:        The directory to save the images in.
            overwrite:  If the folder should be removed if it exists. Default: False
        """

        out_dir = Path(dir)
        if out_dir.is_dir():
            if not overwrite:
                raise FileExistsError(f"{dir} already exists, and overwrite=False")

            rmtree(out_dir)

        os.makedirs(out_dir)
        for idx, img in enumerate(self.img_buffer):
            cv.imwrite(f'{out_dir.as_posix()}/VimbaImage_{idx}.png', img)

    idx = 0

    def get_frame(self):
        """Get the next frame in the sequence
        Args:

        Returns:
            frame (list): RGB values or []
        """

        if self.idx == len(self.img_buffer) - 1:
            self.is_last_frame = True
        else:
            self.is_last_frame = False

        if self.idx >= len(self.img_buffer):
            idx = 0

        self.idx += 1
        return self.img_buffer[idx - 1]
