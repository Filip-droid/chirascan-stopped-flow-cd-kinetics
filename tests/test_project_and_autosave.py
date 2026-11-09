# tests/test_project_and_autosave.py
"""Projects are self-contained (copies of the CSV files), keep the window
state, and the automatic save can be found and restored after a crash."""

import os
import shutil

import numpy as np

from src.modules.analysis import fitting
from src.modules.core.session import AnalysisSession, read_state_file, write_state_file
from src.modules.utils.session_files import AutosaveManager

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV = os.path.join(ROOT, "example", "TT3T-10K00000.csv")


def _session_with_fit(csv_path):
    s = AnalysisSession()
    s.add_files([csv_path])
    s.recompute()
    k = s.result.kinetics_df
    s.fits["one phase association"] = fitting.fit_model(
        "one phase association", s.specs["one phase association"], k["Time"], k["Average CD kinetics"],
        check_starts=0, fingerprint=s.fingerprint)
    return s


def test_project_is_self_contained(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    csv = data / "run.csv"
    shutil.copy(CSV, csv)
    s = _session_with_fit(str(csv))
    s.check_starts = 7
    proj = tmp_path / "p.sfkx"
    s.save_project(str(proj), report_text="my report", view_state={"fit_model": "one phase association", "step": 2})
    assert open(proj, "rb").read(2) == b"\x1f\x8b"            # compressed
    # 1) data file deleted -> the copy stored in the project is used
    os.remove(csv)
    s2 = AnalysisSession()
    assert s2.load_project(str(proj)) == []
    assert any("not found" in n for n in s2.load_notes)
    assert s2.check_starts == 7 and s2.result.fingerprint == s.result.fingerprint
    assert s2.report_text == "my report" and s2.view_state["step"] == 2
    # 2) data file edited -> the stored copy, the fit stays current
    with open(csv, "w") as f:
        f.write(open(CSV).read().replace("4.4345", "9.9999"))
    s3 = AnalysisSession()
    s3.load_project(str(proj))
    assert any("changed" in n for n in s3.load_notes)
    assert s3.is_current(s3.fits["one phase association"])


def test_old_plain_json_projects_still_open(tmp_path):
    s = _session_with_fit(CSV)
    d = s.to_dict()                                           # format 1: settings only, plain JSON
    import json
    p = tmp_path / "old.sfkx"
    p.write_text(json.dumps(d))
    s2 = AnalysisSession()
    assert s2.load_project(str(p)) == [] and s2.result is not None and not s2.fits


def test_crashed_session_is_found(tmp_path):
    alive = set()
    crashed = AutosaveManager(folder=str(tmp_path), session_id="111-aaaa", is_alive=lambda sid: sid in alive)
    crashed.start_session("1.0.0")
    s = _session_with_fit(CSV)
    write_state_file(crashed.autosave_path(), s.build_state(report_text="r"))
    # the instance "crashes": no end_session(); a new instance starts
    new = AutosaveManager(folder=str(tmp_path), session_id="222-bbbb", is_alive=lambda sid: sid in alive)
    new.start_session("1.0.0")
    found = new.find_recoverable()
    assert [f["session"] for f in found] == ["111-aaaa"]
    restored = AnalysisSession()
    restored.load_state(read_state_file(found[0]["path"]))
    assert np.array_equal(restored.fits["one phase association"]["params"], s.fits["one phase association"]["params"])
    new.discard(found[0])
    assert new.find_recoverable() == []
    # a running instance is never offered; a normal end leaves nothing behind
    alive.add("222-bbbb")
    other = AutosaveManager(folder=str(tmp_path), session_id="333-cccc", is_alive=lambda sid: sid in alive)
    write_state_file(new.autosave_path(), {"x": 1})
    assert other.find_recoverable() == []
    new.end_session()
    assert not os.path.exists(new.autosave_path())
