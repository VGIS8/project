#!/usr/bin/env python3

"""Formats the defector python code with yapf according to setup.cfg
"""

import subprocess

if __name__ == '__main__':
    try:
        subprocess.run(['yapf', '-vv', '-ri', 'defector'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to format code: {e}")

