""" Tests for testing the helper functions
"""

import os

# pymba complains in pytest if this isn't set
os.environ["GENICAM_GENTL64_PATH"] = "N/A"

from defector import helpers


def test_twice():
    assert helpers.twice(3) == 6
