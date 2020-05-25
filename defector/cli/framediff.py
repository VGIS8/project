import shutil
import os
from pathlib import Path
from time import sleep

import cv2
from milc import cli

from defector.argument_types import dir_path
from defector.helpers import roi_crop, get_folder, blob_detection, find_contours, background_equalization, make_hist, remove_stationary_contours, get_centroid
from defector.tracker import Tracker


@cli.argument('-d', '--distance', help='The distance in frames to diff over', type=int, default=1)
@cli.argument('-r', '--roi', help='Crop ROI of all images', action='store_false')
@cli.argument('-f', '--force', help='Remove output directory if it exists. !!THIS REMOVES THE ENTIRE DIRECTORY!!', action='store_true')
@cli.argument('-i', '--input', type=dir_path, help='Directory containing the image sequence. Has to end in a number sequence', required=True)
@cli.argument('-o', '--output', type=Path, help='Output directory to save images sequence in', default='framediff_output')
@cli.subcommand("Generates sequence of frame differences from input image sequence")
def framediff(cli):
    """
    Create a series of frame differences between all subsequent frames of VirtCam.
    """

    if cli.config.framediff.output.is_dir():
        if cli.config.framediff.force:
            shutil.rmtree(cli.config.framediff.output)
            while cli.config.framediff.output.is_dir():
                pass
            sleep(0.5)
        else:
            cli.log.error(f'{str(cli.config.framediff.output)} already exists, and overwrite isn\'t forced')
            return False
    os.makedirs(cli.config.framediff.output)

    images = get_folder(cli.config.framediff.input.resolve())

    ############# test implementation of track ##################
    center_points = []
    #size = None

    # Create Object Tracker
    tracker = Tracker(50, 5, 5, 100, 0.5)

    # Variables initialization
    skip_frame_count = 0
    track_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 127, 255), (127, 0, 255), (127, 0, 127)]

    ##############################################################

    first_run = True
    for idx, img in enumerate(images[:-cli.config.framediff.distance]):
        background = cv2.imread(img, cv2.IMREAD_COLOR)
        frame = cv2.imread(images[idx + cli.config.framediff.distance], cv2.IMREAD_COLOR)

        if cli.config.framediff.roi:
            first_run, background = roi_crop(background, first_run)

        contours, center_img = find_contours(background)

        stationary_threshhold = 5
        contours_found = len(contours)
        contours = remove_stationary_contours(contours, stationary_threshhold, 5, 10)
        print(f"Contours: {len(contours)} moving | {contours_found - len(contours)} stationary")

        centroids = [get_centroid(c) for c in contours]

        cv2.drawContours(center_img, contours, -1, (0, 0, 255), 2)

        for centroid in centroids:
            # draw the radius of the points, deciding if points are considered stationary
            cv2.circle(center_img, (centroid[0][0], centroid[1][0]), stationary_threshhold, (0, 255, 0), 1)

        ################## tracker ###############
        tracker.Update(contours)

        # For identified object tracks draw tracking line
        # Use various colors to indicate different track_id
        for i in range(len(tracker.tracks)):
            if (len(tracker.tracks[i].trace) > 1):
                for j in range(len(tracker.tracks[i].trace) - 1):
                    # Draw trace line
                    x1 = int(tracker.tracks[i].trace[j][0][0])
                    y1 = int(tracker.tracks[i].trace[j][1][0])
                    x2 = int(tracker.tracks[i].trace[j + 1][0][0])
                    y2 = int(tracker.tracks[i].trace[j + 1][1][0])
                    clr = tracker.tracks[i].track_id % 9
                    cv2.line(center_img, (x1, y1), (x2, y2), track_colors[clr], 1)
                if tracker.tracks[i].point is not None:
                    cv2.line(center_img, (x2, y2), (tracker.tracks[i].point[0][0], tracker.tracks[i].point[1][0]), track_colors[clr], 1)

        # Display the resulting tracking frame

        cv2.imshow('Tracking', center_img)
        cv2.waitKey(10)

        # Check for key strokes
        k = cv2.waitKey(50) & 0xff
        if k == 27:  # 'esc' key has been pressed, exit program.
            break
        if k == 112:  # 'p' has been pressed. this will pause/resume the code.
            pause = not pause
            if (pause is True):
                print("Code is paused. Press 'p' to resume..")
                while (pause is True):
                    # stay in this loop until
                    key = cv2.waitKey(30) & 0xff
                    if key == 112:
                        pause = False
                        print("Resume code..!!")
                        break
        ###########################################
        cv2.imwrite(str(cli.config.framediff.output.joinpath(f'out{idx}.png')), center_img)
    cv2.destroyAllWindows()
