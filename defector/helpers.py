"""A collection of helper functions used for the main program
"""

from typing import Optional
from pathlib import Path
from glob import glob

import re

import cv2
import numpy as np
from scipy.spatial.distance import euclidean, cdist
from matplotlib import pyplot as plt

from pymba import Vimba, VimbaException, Frame

# todo add more colours
PIXEL_FORMATS_CONVERSIONS = {
    'BayerRG8': cv2.COLOR_BAYER_RG2RGB,
}


def display_frame(frame: Frame, delay: Optional[int] = 1) -> None:
    """Displays the acquired frame.

    Args:
        frame: The frame object to display.
        delay: Display delay in milliseconds, use 0 for indefinite.
            Default 1
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
            Default 1
        cam: The index(int) or camera_id(str)
            Default 0

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


def get_plug_crop(frame):
    x = 0
    y = 0
    order = -1

    w, h = search_vertical(frame, order)

    return x, y, w, h


transformation_matrix = None
crop_size = None
crop_params = None


def roi_crop(frame, first_run):
    """ Takes an image and returns a cropped image
        Crops frames to remove background

        Args:
            img: An gray scale openCV image

        Returns:
            A cropped image
    """
    global transformation_matrix
    global crop_size
    global crop_params

    if first_run:
        first_run = False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshed_img = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
        # find contours and get the external one

        kernel = np.ones((15, 15), np.uint8)
        opening = cv2.morphologyEx(threshed_img, cv2.MORPH_OPEN, kernel)

        contours, hier = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        chosen_contour = max(contours, key=cv2.contourArea)

        rect = cv2.minAreaRect(chosen_contour)

        # Get the transformation matrix and crop size for the vial in frame
        transformation_matrix, crop_size = get_transform_params(frame, rect)

        # Crop out the right side of the frame if over 2% of the frame is still background
        rotated = cv2.warpPerspective(frame, transformation_matrix, crop_size, None, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT, (255, 255, 255))
        if check_for_black(rotated) > 2.00:
            crop_params = get_plug_crop(rotated)

    else:
        rotated = cv2.warpPerspective(frame, transformation_matrix, crop_size, None, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT, (255, 255, 255))

    if crop_params is not None:
        rotated = second_crop(rotated, crop_params)

    return first_run, rotated


def second_crop(frame, crop_params):

    x, y, w, h = crop_params

    cropped = frame[y:y + h, x:x + w]

    return cropped


def check_for_black(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshed = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    not_black_count = cv2.countNonZero(threshed)

    rows, cols = gray.shape
    all_pixels = rows * cols

    black_count = all_pixels - not_black_count
    black_ratio = (black_count / all_pixels) * 100

    return black_ratio


def search_vertical(frame, direction=-1):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshed = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    rows, cols = gray.shape
    crop_row = rows

    if direction not in [-1, 1]:
        raise ValueError("direction has to be -1 or 1")

    crop_col = 0
    for col in range(cols)[::direction]:
        vertical_pixels = []
        for row in range(rows):
            vertical_pixels.append(threshed[row, col])

        non_black_vertical = np.count_nonzero(vertical_pixels)
        black_vertical = len(vertical_pixels) - non_black_vertical

        if black_vertical < 5:
            crop_col = col
            # start_point = (0, crop_col)
            # end_point = (crop_row, col)

            #            image = cv2.line(frame, start_point, end_point, (0, 0, 255), 10)
            #            cv2.imshow("image", image)
            #            cv2.waitKey(0)
            break
        else:
            pass

    return crop_col, crop_row


def get_transform_params(img, rect):
    # find rotated rectangle
    rbox = order_points(cv2.boxPoints(rect))

    # output of minAreaRect is unreliable for already axis aligned rectangles.
    # get width and height of the detected rectangle
    width = np.linalg.norm([rbox[0, 0] - rbox[1, 0], rbox[0, 1] - rbox[1, 1]])
    height = np.linalg.norm([rbox[0, 0] - rbox[-1, 0], rbox[0, 1] - rbox[-1, 1]])
    src_pts = rbox.astype(np.float32)

    # coordinate of the points in box points after the rectangle has been straightened
    # this step needs order_points to be called on src
    dst_pts = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")

    transformation_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    return transformation_matrix, (width, height)


def order_points(pts):
    # Sort the points based on their x-coordinates
    xSorted = pts[np.argsort(pts[:, 0]), :]

    # Grab the left-most and right-most points from the sorted x-coordinate points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]

    # Now, sort the left-most coordinates according to their y-coordinates so we can grab the top-left and bottom-left
    # points, respectively
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost

    # Now that we have the top-left coordinate, use it as an anchor to calculate the Euclidean distance between the
    # top-left and right-most points; by the Pythagorean theorem, the point with the largest distance will be
    # our bottom-right point
    D = cdist(tl[np.newaxis], rightMost, "euclidean")[0]
    (br, tr) = rightMost[np.argsort(D)[::-1], :]

    # return the coordinates in top-left, top-right,
    # bottom-right, and bottom-left order
    return np.asarray([tl, tr, br, bl], dtype=pts.dtype)


def background_equalization(frame, kernel_size):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Create structuring element and apply the black hat transform
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    equalized = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)

    return equalized


def make_hist(frame):
    plt.hist(frame.ravel(), 256, [0, 256])
    plt.show()
    return frame


def get_centroid(contours):
    M = cv2.moments(contours)

    # compute the centroid of the contour
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
    else:
        # set values instead
        cX, cY = 0, 0

    c_all = np.array([[cX], [cY]])
    return c_all


def find_contours(frame):

    kernel_size = 25
    ca = background_equalization(frame, kernel_size)

    _, binary = cv2.threshold(ca, 7, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # blobbed = blob_detection(closing)

    # Find Canny edges
    # edged = cv2.Canny(closing, 120, 255)

    contours, hierarchy = cv2.findContours(opening, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    for idx, c in enumerate(contours):
        if len(c) > 150:
            if cv2.contourArea(c) > 200:
                del contours[idx]

    # cv2.drawContours(frame, contours, -1, (0, 0, 255), 2)

    # loop over the contours
    for i, c in enumerate(contours):

        centroid = get_centroid(c)

        # draw the  center of the shape on the image
        cv2.circle(frame, (centroid[0][0], centroid[1][0]), 1, (255, 0, 0), 2)

    return contours, frame


# [[x,y], instances, found(bool)]
reference_points = None


class ReferencePoint:
    def __init__(self, point, area=0):
        self.point = point
        self.life = 0
        self.skipped_frames = 0
        self.found = False
        self.area = area


reference_points = None


def remove_stationary_contours(contours, thresh=0.5, interval=10, max_skipped_frames=1, max_referance_points=100):  # noqa: C901
    global reference_points
    """ Removes contours that don't move
        more than threshhold over interval frames

        Args:
            contours: List of contours to filter.
            thresh: Max distance a contour can move while still being considered stationary
            interval: The number of concecutive frames it has to be stationary for

        Returns:
            contours: List of contours with stationary contours removed
    """

    centroids = [get_centroid(contour) for contour in contours]
    unassigned_centroids = centroids

    # 0: Get all centroids

    # 2: If first time, take these as reference point
    # 3: If new centroids are within x range of reference point, consider them the same as reference point
    # 4: If points aren't within any reference point, consider them as new reference points
    # 5: If no points are wihtin x range of reference point, discard reference point

    # If we don't have any history
    if reference_points is None:
        reference_points = [ReferencePoint(centroid) for centroid in unassigned_centroids]
        return contours

    # Set "found" state to false
    for point in reference_points:
        point.found = False

    discarded_contours = []
    assigned_centroids = []
    for idx_c, centroid in enumerate(unassigned_centroids):
        for idx_rp, point in enumerate(reference_points):
            # If the centroid is within <thresh> of a reference point, consider it the reference point
            # print(euclidean(centroid, point.point))
            if euclidean(centroid, point.point) <= thresh:
                if idx_c not in assigned_centroids:
                    assigned_centroids.append(idx_c)
                point.life += 1
                point.found = True
                point.skipped_frames = 0
                if point.life >= interval:
                    if idx_c not in discarded_contours:
                        discarded_contours.append(idx_c)

    # Remove assigned points from the unassigned list
    for idx_c in sorted(assigned_centroids, reverse=True):
        del unassigned_centroids[idx_c]

    # Assign any unassigned centroids as new reference points
    for centroid in unassigned_centroids:
        if len(reference_points) < max_referance_points:
            reference_points.append(ReferencePoint(centroid))
        else:
            pass
            # print("Max reference points reached")

    discarded_reference_points = []
    # Remove any reference points that haven't been found for <max_skipped_frames> frames
    for idx_rp, point in enumerate(reference_points):
        if not point.found:
            point.skipped_frames += 1
            if point.skipped_frames > max_skipped_frames:
                if idx_rp not in discarded_reference_points:
                    discarded_reference_points.append(idx_rp)

    for idx_rp in sorted(discarded_reference_points, reverse=True):
        del reference_points[idx_rp]

    # Remove contours that appear stationary
    for idx_c in sorted(discarded_contours, reverse=True):
        del contours[idx_c]
        pass

    return contours


def blob_detection(frame):

    # Setup SimpleBlobDetector parameters.
    params = cv2.SimpleBlobDetector_Params()

    params.minThreshold = 0
    params.maxThreshold = 255
    params.filterByArea = True
    params.minArea = 15
    # params.filterByCircularity = False
    # params.minCircularity = 0.1
    # params.filterByConvexity = False
    # params.minConvexity = 0.87
    # params.filterByInertia = False
    # params.minInertiaRatio = 0.01

    # Create a detector with the parameters
    ver = (cv2.__version__).split('.')
    if int(ver[0]) < 3:
        detector = cv2.SimpleBlobDetector(params)
    else:
        detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs.
    keypoints = detector.detect(frame)

    # Draw detected blobs as red circles.
    im_with_keypoints = cv2.drawKeypoints(frame, keypoints, np.array([]), (0, 0, 255), 2)

    return im_with_keypoints


def sort_key_func(s):
    """Return the first number you find in string. 0 if not"""
    nums = re.findall('[0-9]+', Path(s).name)
    if nums == []:
        return 0
    else:
        return int(nums[0])


def get_folder(folder, types=['jpg', 'png']):
    folder = Path(folder)

    images = []
    for e in types:
        images.extend(glob(f'{folder}/*.{e}'))
    images.sort(key=sort_key_func)
    return images
