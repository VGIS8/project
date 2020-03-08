"""Formats the defector python code with yapf according to setup.cfg
"""

import subprocess

def format():
    try:
        subprocess.run(['yapf', '-vv', '-ri', 'defector'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to format code: {e}")

if __name__ == '__main__':
    format()
