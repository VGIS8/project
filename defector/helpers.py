"""A collection of helper functions used for the main program
"""

from typing import Optional
from pathlib import Path
from glob import glob

import re

import cv2
import numpy as np

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

    img = cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)

    _, threshed_img = cv2.threshold(img, 40, 255, cv2.THRESH_BINARY)
    # find contours and get the external one

    kernel = np.ones((15, 15), np.uint8)
    closing = cv2.morphologyEx(threshed_img, cv2.MORPH_CLOSE, kernel)

    contours, hier = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    chosen_contour = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(chosen_contour)
    # draw a green rectangle to visualize the bounding rect

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
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(25,25))
    # Apply the top hat transform
    tophat = cv2.morphologyEx(frame, cv2.MORPH_TOPHAT, kernel)

    # Apply the black hat transform
    blackhat = cv2.morphologyEx(frame, cv2.MORPH_BLACKHAT, kernel)

    return frame

def find_contours(frame):
    # find contours in the thresholded image
    #cnts = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #contours, hierarchy = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # loop over the contours
    #for c in contours:
        # compute the center of the contour
    M = cv2.moments(frame)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # put text and highlight the center
    #cv2.circle(img, (cX, cY), 5, (255, 255, 255), -1)
    #cv2.putText(img, "centroid", (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # draw the contour and center of the shape on the image
    #cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
    cv2.circle(frame, (cX, cY), 7, (255, 255, 255), -1)
    cv2.putText(frame, "center", (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return frame

def blob_detection(frame):

    # Setup SimpleBlobDetector parameters.
    params = cv2.SimpleBlobDetector_Params()

    # Change thresholds
    params.minThreshold = 0
    params.maxThreshold = 255

    # Filter by Area.
    params.filterByArea = False
#    params.minArea = 1500

    # Filter by Circularity
    params.filterByCircularity = True
    params.minCircularity = 0.1

    # Filter by Convexity
    params.filterByConvexity = False
    params.minConvexity = 0.87

    # Filter by Inertia
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
    im_with_keypoints = cv2.drawKeypoints(frame, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

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
