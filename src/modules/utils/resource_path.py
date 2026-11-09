# src/modules/utils/resource_path.py
"""Path of a bundled resource, both when run from source and from the
PyInstaller build (where the files are unpacked under sys._MEIPASS)."""

import os
import sys


def project_root():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def resource_path(*parts):
    return os.path.join(project_root(), "resources", *parts)


def example_path(*parts):
    """The example data: the folder example/ of the repository (shared with the notebook);
    bundled under the same name in the installed program."""
    return os.path.join(project_root(), "example", *parts)
