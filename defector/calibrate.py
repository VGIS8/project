"""Provides functions to get camera matrix and calibration vector
"""

import numpy as np
import cv2 as cv
import glob


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

    def __init__(self, image_path, file_types=None, checker_board_size=None):
        if file_types is not None:
            self.file_types = file_types

        if checker_board_size is not None:
            self.checker_board_size = checker_board_size

        self.objpoints = np.zeros((checker_board_size[0] * checker_board_size[1], 3), np.float32)
        self.objpoints[:, :2] = np.mgrid[0:checker_board_size[0], 0:checker_board_size[1]].T.reshape(-1, 2)

        self.images = [glob.glob(f'{image_path}/*.{e}') for e in self.file_types]

    frame_cnt = 0

    def get_frame(self):
        global frame_cnt
        overflow = False

        if frame_cnt >= len(self.images):
            frame_cnt = 0
            overflow = True

        frame = self.images[frame_cnt]
        frame_cnt += 1

        return cv.imread(frame), overflow

    def checker_calibrate(self):
        overflow = False
        while not overflow:
            img, overflow = self.get_frame()
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            # Find the chess board corners
            ret, corners = cv.findChessboardCorners(gray, (9, 6), None)
            # If found, add object points, image points (after refining them)
            if ret:
                self.imgpoints.append(corners)

        ret, self.camera_matrix, self.distortion_vector, rvecs, tvecs = cv.calibrateCamera(self.objpoints, imgpoints, gray.shape[::-1], None, None)
