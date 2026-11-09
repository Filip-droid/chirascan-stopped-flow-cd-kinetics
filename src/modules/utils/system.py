# src/modules/utils/system.py
"""Opening files and folders with the operating system."""

import os
import subprocess
import sys


def open_with_system(path):
    """Open a file or folder with the program Windows (or the desktop) associates with it."""
    if sys.platform == "win32":
        os.startfile(path)                     # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
