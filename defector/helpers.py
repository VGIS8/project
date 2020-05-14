"""A collection of helper functions used for the main program
"""

from typing import Optional
from pathlib import Path
from glob import glob

import re

import cv2
import numpy as np
from scipy.spatial.distance import euclidean
# from matplotlib import pyplot as plt

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


def roi_crop(img, size=None):
    """ Takes an image and returns a cropped image
        Crops frames to remove background

        Args:
            img: An gray scale openCV image

        Returns:
            A cropped image
    """
    # img = cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, threshed_img = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
    # find contours and get the external one

    kernel = np.ones((15, 15), np.uint8)
    closing = cv2.morphologyEx(threshed_img, cv2.MORPH_CLOSE, kernel)

    contours, hier = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    chosen_contour = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(chosen_contour)

    if size is None:
        size = [x, y, w, h]
    else:
        x, y, w, h = size

    # create mask and draw filled rectangle from contour
    mask = np.zeros(img.shape, np.uint8)

    cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), cv2.FILLED)
    # apply mask
    dst = cv2.bitwise_and(img, mask)

    # crop image to mask
    img = dst[y:y + h, x:x + w]

    return size, img


def correct_ambient(frame):
    # Structuring element
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))

    # Apply the black hat transform
    corrected = cv2.morphologyEx(frame, cv2.MORPH_BLACKHAT, kernel)

    return corrected


def draw_lines(frame, background):

    return frame


def make_hist(frame):
    # plt.hist(frame.ravel(), 256, [0, 256])
    # plt.show()
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

    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # Find Canny edges
    ca = correct_ambient(gray)

    a = np.double(ca)
    b = a - 15
    darker = np.uint8(b)

    _, binary = cv2.threshold(darker, 120, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bigger = cv2.dilate(binary, kernel)

    edged = cv2.Canny(bigger, 120, 255)

    # cv2.imshow("org", frame)
    # cv2.imshow("corrected", bigger)
    # cv2.imshow("edged", edged)
    # cv2.waitKey(1)

    contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    print("Number of Contours found = " + str(len(contours)))

    max_idx = 0
    max_area = 0
    for idx, contour in enumerate(contours):
        x = cv2.contourArea(contour)
        try:
            if x > max_area:
                max_area = x
                max_idx = idx
        except TypeError:
            continue

    del contours[max_idx]

    #cv2.drawContours(frame, contours, -1, (0, 0, 255), 2)

    #centers = []
    # loop over the contours
    for i, c in enumerate(contours):
    
        centroid = get_centroid(c)
        #centers.append((centroid[0][0], centroid[1][0]))

        # draw the  center of the shape on the image
        cv2.circle(frame, (centroid[0][0], centroid[1][0]), 2, (255, 0, 0), 1)

    return contours, frame


# [[x,y], instances, found(bool)]
reference_points = None


class ReferencePoint:
    def __init__(self, point):
        self.point = point
        self.life = 0
        self.skipped_frames = 0
        self.found = False


reference_points = None


def remove_stationary_contours(contours, thresh=0.5, interval=10, max_skipped_frames=1, max_referance_points=100):
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
            #print(euclidean(centroid, point.point))
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

    # Change parameters
    params.minThreshold = 0
    params.maxThreshold = 255
    params.filterByArea = False
    params.minArea = 1500
    params.filterByCircularity = True
    params.minCircularity = 0.1
    params.filterByConvexity = False
    params.minConvexity = 0.87
    params.filterByInertia = False
    params.minInertiaRatio = 0.01

    # Create a detector with the parameters
    ver = (cv2.__version__).split('.')
    if int(ver[0]) < 3:
        detector = cv2.SimpleBlobDetector(params)
    else:
        detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs.
    keypoints = detector.detect(frame)
    # Draw detected blobs as red circles.
    # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
    im_with_keypoints = cv2.drawKeypoints(frame, keypoints, np.array([]), (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

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
