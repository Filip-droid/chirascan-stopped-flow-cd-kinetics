# tests/test_platform.py
"""Things that differ between Windows and macOS: the per-user data folder and
the default place of the Excel export."""

import os
import sys
from types import SimpleNamespace

from src.modules.export.excel_export import default_output_path
from src.modules.utils import app_logger


def test_app_data_dir_per_platform(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "win32")
    assert app_logger.app_data_dir() == os.path.join(str(tmp_path), "StoppedFlowKinetiX")
    monkeypatch.setattr(sys, "platform", "darwin")
    assert app_logger.app_data_dir().endswith(os.path.join("Library", "Application Support", "StoppedFlowKinetiX"))
    monkeypatch.setattr(sys, "platform", "linux")
    assert app_logger.app_data_dir().endswith(".stoppedflowkinetix")


def test_export_goes_to_documents_when_the_data_folder_is_read_only(monkeypatch, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    f = SimpleNamespace(path=str(data / "run.csv"))
    assert default_output_path([f]) == os.path.join(str(data), "results CD.xlsx")
    monkeypatch.setattr(os, "access", lambda p, mode: False)        # e.g. the example inside the app
    home = tmp_path / "home"
    (home / "Documents").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    assert default_output_path([f]) == os.path.join(str(home), "Documents", "results CD.xlsx")
