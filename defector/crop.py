import numpy as np
import cv2

def roi_crop():
    # Load an color image in grayscale
    img = cv2.imread('clean_1.png')

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

    cv2.imshow("contours", crop_img)

    return crop_img

