"""A collection of helper functions used for the main program
"""

from typing import Optional

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


def roi_crop(img):
    """ Takes an image and returns a cropped image
        Crops frames to remove background

        Args:
            img: An openCV image
        
        Returns:
            A cropped image
    """

    ret, threshed_img = cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 40, 255, cv2.THRESH_BINARY)
    # find contours and get the external one

    kernel = np.ones((15, 15), np.uint8)
    closing = cv2.morphologyEx(threshed_img, cv2.MORPH_CLOSE, kernel)

    contours, hier = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    chosen_contour = max(contours, key=len)

    x, y, w, h = cv2.boundingRect(chosen_contour)
    # draw a green rectangle to visualize the bounding rect

    # get the min area rect
    rect = cv2.minAreaRect(chosen_contour)
    box = cv2.boxPoints(rect)

    # convert all coordinates floating point values to int
    box = np.int0(box)

    # create mask and draw filled rectangle from contour
    mask = np.zeros(img.shape, np.uint8)
    cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), cv2.FILLED)

    # apply mask
    dst = cv2.bitwise_and(img, mask)

    # crop image to mask
    crop_img = dst[y:y + h, x:x + w]

    return crop_img
