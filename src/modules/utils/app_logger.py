# src/modules/utils/app_logger.py
"""Application log: a rotating file in the user's local application-data folder
(%LOCALAPPDATA%\\StoppedFlowKinetiX\\logs on Windows) plus the console."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.version import APP_NAME

_configured = False


def app_data_dir():
    """A persistent, writable per-user folder of the application."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, APP_NAME)
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    return os.path.join(os.path.expanduser("~"), "." + APP_NAME.lower())


def log_file_path():
    return os.path.join(app_data_dir(), "logs", "application.log")


def setup_logging(level=logging.INFO):
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s: %(message)s")
    try:
        os.makedirs(os.path.dirname(log_file_path()), exist_ok=True)
        fh = RotatingFileHandler(log_file_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass
    if sys.stderr is not None:                     # no console in the --windowed build
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        root.addHandler(sh)
    _configured = True


def get_logger(name):
    return logging.getLogger(name)
