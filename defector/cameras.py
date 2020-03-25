"""Provides functions to get camera matrix and calibration vector
"""

import numpy as np
from pathlib import Path
import cv2 as cv
import glob
import re


def sort_key_func(s):
    '''Return the first number you find in string. 0 if not'''
    nums = re.findall('[0-9]+', Path(s).name)
    if nums == []:
        return 0
    else:
        return int(nums[0])


class VirtCam:
    """Provides a camera compatible class, that instead streas images from a folder"""

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
            last (boolean): True if the returned frame is the last in the current sequence. False otherwise.
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

    def checker_calibrate(self):
        while not self.is_last_frame:
            img = self.get_frame()
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            # Find the chess board corners
            ret, corners = cv.findChessboardCorners(gray, (9, 6), None)
            # If found, add object points, image points (after refining them)
            if ret:
                self.imgpoints.append(corners)

        ret, self.camera_matrix, self.distortion_vector, rvecs, tvecs = cv.calibrateCamera(self.objpoints, self.imgpoints, gray.shape[::-1], None, None)
