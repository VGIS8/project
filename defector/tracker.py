'''
    File name               : tracker.py
    File Description        : Tracker Using Kalman Filter & Hungarian Algorithm
    Original Author         : Srini Ananthakrishnan
    Date created            : 2017-07-14
    Defector implementation : 2020-05-10
    Defector implementer    : VGIS8 20GR840 AAU
    Python Version          : 3.6

    The classes in this file are re-implementations of the work done by Srini Ananthakrishnan.
    It has been re-implemented to work with our project
'''

import numpy as np

from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import euclidean
from filterpy.kalman import KalmanFilter

from defector.helpers import get_centroid
from cv2 import contourArea


class Track:
    """Track class for every object to be tracked
    Attributes:
        None
    """
    def __init__(self, prediction, trackIdCount, contour_size):
        """Initialize variables used by Track class
        Args:
            prediction: predicted centroids of object to be tracked
            trackIdCount: identification of each track object
        Return:
            None
        """
        self.track_id = trackIdCount  # identification of each track object
        self.KF = KalmanFilter(2, 2)  # KF instance to track this object
        self.dt = 0.005
        self.KF.F = np.array([[1, self.dt], [0, 1]])  # State transition matrix
        self.KF.P = np.diag((3.0, 3.0))  # covarianse matrix
        self.KF.H = np.array([[1, 0], [0, 1]])  # matrix in observation equations / measurment function

        self.prediction = np.asarray(prediction)  # predicted centroids (x,y)
        self.previous_size = contour_size  # the size of the previous contour
        self.skipped_frames = 0  # number of frames skipped undetected
        self.trace = []  # trace path
        self.point = []  # the last point associated with the trace


class Tracker:
    """Tracker class that updates track vectors of object tracked
    Attributes:
        None
    """
    def __init__(self, dist_thresh, max_frames_to_skip, max_trace_length, trackIdCount, size_weight=0.2, distance_weight=1.0):
        """Initialize variable used by Tracker class
        Args:
            dist_thresh: distance threshold. When exceeds the threshold,
                         track will be deleted and new track is created
            max_frames_to_skip: maximum allowed frames to be skipped for
                                the track object undetected
            max_trace_lenght: trace path history length
            trackIdCount: identification of each track object
        Return:
            None
        """
        self.dist_thresh = dist_thresh
        self.max_frames_to_skip = max_frames_to_skip
        self.max_trace_length = max_trace_length
        self.tracks = []
        self.trackIdCount = trackIdCount
        self.size_weight = size_weight
        self.distance_weight = distance_weight

    def get_cost_matrix(self, size, detections):
        cost_matrix = np.zeros(shape=size)

        centroids = [get_centroid(c) for c in detections]

        for i in range(len(self.tracks)):
            for j in range(len(centroids)):
                try:
                    distance = euclidean(self.tracks[i].prediction, centroids[j])
                    size_diff = np.abs(self.tracks[i].previous_size - contourArea(detections[j]))

                    # Let's average the squared ERROR
                    distance_cost = (0.5) * distance

                    cost = self.distance_weight * distance_cost - self.size_weight * size_diff

                    cost_matrix[i][j] = cost
                except NotADirectoryError:  # placed here to see what error the above try is trying to catch
                    pass

        return cost_matrix

    def Update(self, detections):  # noqa: C901
        """Update tracks vector using following steps:
            - Create tracks if no tracks vector found
            - Calculate cost using sum of square distance
              between predicted vs detected centroids
            - Using Hungarian Algorithm assign the correct
              detected measurements to predicted tracks
              https://en.wikipedia.org/wiki/Hungarian_algorithm
            - Identify tracks with no assignment, if any
            - If tracks are not detected for long time, remove them
            - Now look for un_assigned detects
            - Start new tracks
            - Update KalmanFilter state, lastResults and tracks trace
        Args:
            detections: detected contours of object to be tracked
        Return:
            None
        """

        # Create tracks if no tracks vector found
        if (len(self.tracks) == 0):
            for i in range(len(detections)):
                track = Track(get_centroid(detections[i]), self.trackIdCount, contourArea(detections[i]))
                self.trackIdCount += 1
                self.tracks.append(track)

        # Calculate cost using sum of square distance between
        # predicted vs detected centroids
        N = len(self.tracks)
        M = len(detections)
        cost = self.get_cost_matrix((N, M), detections)

        # Using Hungarian Algorithm assign the correct detected measurements
        # to predicted tracks
        row_ind, col_ind = linear_sum_assignment(cost)

        assignment = [-1 for _ in range(N)]
        for i in range(len(row_ind)):
            assignment[row_ind[i]] = col_ind[i]

        # Identify tracks with no assignment, if any
        un_assigned_tracks = []
        for i in range(len(assignment)):
            if (assignment[i] != -1):
                # check for cost distance threshold.
                # If cost is very high then un_assign (delete) the track
                if (cost[i][assignment[i]] > self.dist_thresh):
                    assignment[i] = -1
                    un_assigned_tracks.append(i)
            else:
                self.tracks[i].skipped_frames += 1

        # If tracks are not detected for long time, remove them
        del_tracks = []
        for i in range(len(self.tracks)):
            if (self.tracks[i].skipped_frames > self.max_frames_to_skip):
                del_tracks.append(i)
        if len(del_tracks) > 0:  # only when skipped frame exceeds max
            for id in del_tracks:
                if id < len(self.tracks):
                    del self.tracks[id]
                    del assignment[id]
                else:
                    print("ERROR: id is greater than length of tracks")

        # Now look for un_assigned detects
        un_assigned_detects = []
        for i in range(len(detections)):
            if i not in assignment:
                un_assigned_detects.append(i)

        # Start new tracks
        if (len(un_assigned_detects) != 0):
            for i in range(len(un_assigned_detects)):
                track = Track(get_centroid(detections[un_assigned_detects[i]]), self.trackIdCount, contourArea(detections[un_assigned_detects[i]]))
                self.trackIdCount += 1
                self.tracks.append(track)

        # Update KalmanFilter state, lastResults and tracks trace
        for i in range(len(assignment)):
            self.tracks[i].KF.predict()

            if (assignment[i] != -1):
                self.tracks[i].skipped_frames = 0
                self.tracks[i].KF.update(get_centroid(detections[assignment[i]]))
                self.tracks[i].prediction = self.tracks[i].KF.x
                self.tracks[i].previous_size = contourArea(detections[assignment[i]])
                self.tracks[i].point = get_centroid(detections[assignment[i]])
            else:
                self.tracks[i].KF.update(None)
                self.tracks[i].prediction = self.tracks[i].KF.x
                self.tracks[i].point = None

            if (len(self.tracks[i].trace) > self.max_trace_length):
                for j in range(len(self.tracks[i].trace) - self.max_trace_length):
                    del self.tracks[i].trace[j]

            self.tracks[i].trace.append(self.tracks[i].prediction)
            # self.tracks[i].KF.lastResult = self.tracks[i].prediction
