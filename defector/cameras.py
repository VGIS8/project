"""Provides functions to get camera matrix and calibration vector
"""

from shutil import rmtree
import os
from pathlib import Path
from time import sleep

import cv2 as cv
from pymba import Vimba, Frame


class PymbaCam:
    PIXEL_FORMATS_CONVERSIONS = {
        'BayerRG8': cv.COLOR_BAYER_RG2RGB,
    }

    def __init__(self, mode='Continuous', cam_idx=0):
        self.vimba = Vimba()
        self.vimba.startup()
        self.camera = self.vimba.camera(cam_idx)

        self.is_last_frame = True
        self.framerate = 0
        self.framerate_sum = 0
        self.img_buffer = []
        self.img_IDs = []
        if mode not in 'Continuous':  # SingleFrame']:
            raise NotImplementedError(f"{mode} is not a valid mode or not implemented. Use Continuous")

        self.camera.open()
        exposure = self.camera.feature('ExposureTimeAbs')
        exposure.value = 1000
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

        self.img_IDs.append([frame.data.frameID, False])

        # If the frame is incomplte, discard it (VmbFrame_t.receiveStatus does not equal VmbFrameStatusComplete)
        if frame.data.receiveStatus == -1:
            print(f"Incomplete frame: ID{frame.data.frameID}")
            return

        # get a copy of the frame data
        try:
            image = frame.buffer_data_numpy()
        except NotImplementedError:
            print(f"Empty frame: ID{frame.data.frameID}")
            return

        # convert colour space if desired
        try:
            image = cv.cvtColor(image, self.PIXEL_FORMATS_CONVERSIONS[frame.pixel_format])
        except KeyError:
            pass

        self.img_IDs[-1][1] = True
        self.framerate_sum += self.camera.AcquisitionFrameRateAbs
        self.img_buffer.append(image)

    def capture(self, num_of_images=100):
        print("Started capture")
        self.img_buffer = []
        self.camera.start_frame_acquisition()

        # stream images for a while... stop one image before, as an additional frame is captured when acquisition is stopped
        while len(self.img_buffer) < num_of_images - 1:
            sleep(0.001)

        self.camera.stop_frame_acquisition()
        sleep(0.5)

        self.framerate = self.framerate_sum / len(self.img_buffer)
        print(f"Average framerate: {self.framerate}")
        print(f"Good frames {len(self.img_buffer)}/{len(self.img_IDs)}")

    def save_images(self, dir, overwrite=False):
        """Save the image buffer to a folder of frames

        Args:
            dir:        The directory to save the images in.
            overwrite:  If the folder should be removed if it exists. Default: False
        """
        print("Saving images:")

        out_dir = Path(dir)
        if out_dir.is_dir():
            if not overwrite:
                raise FileExistsError(f"{dir} already exists, and overwrite=False")

            rmtree(out_dir)
            while out_dir.is_dir():
                pass

        os.makedirs(out_dir)
        with open(f'{out_dir.as_posix()}/framerate', 'w') as framerate_file:
            framerate_file.write(str(self.framerate))

        for img in self.img_buffer:

            # Get the next valid frame ID
            idx = self.img_IDs.pop(0)
            while not idx[1]:
                idx = self.img_ID
                self.img_IDs.pop(0)
                print('a')
            idx = idx[0]

            cv.imwrite(f'{out_dir.as_posix()}/VimbaImage_{idx}.png', img)
            print(f"\t{out_dir.as_posix()}/VimbaImage_{idx}.png")
        print('All images saved')

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
