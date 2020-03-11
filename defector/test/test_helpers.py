""" Tests for testing the helper functions
"""

import os

# pymba complains in pytest if this isn't set
os.environ["GENICAM_GENTL64_PATH"] = "N/A"  # noqa: E402 we have to do this before importing helpers

from defector import helpers


def test_twice():
    assert helpers.twice(3) == 6
