#!/usr/bin/env python3
"""This file has functions used as argument types, in cases where no type exists
"""

from pathlib import Path
from argparse import ArgumentError


def dir_path(path):
    """Tests if the given path is a directory

    Args:
        path (str): A string to test if it's a path

    Returns:
        path (Path): A Path() object with the path when path is a dir, False otherwise
    """
    if Path(path).is_dir():
        return Path(path)
    else:
        raise ArgumentError(f'{path} is not a directory')
