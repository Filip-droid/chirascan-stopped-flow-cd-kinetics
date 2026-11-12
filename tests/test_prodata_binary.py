# tests/test_prodata_binary.py
"""Binary Chirascan files (*.dsx), spectra, and the recognition of kinetics vs
spectra. The .dsx files are written here in the layout of the instrument (see
src/modules/data_io/prodata_binary.py); real measurements are checked by
tools/check_dsx_against_csv.py and, if the environment variable
SFK_DSX_DATA names a folder with .dsx + .csv pairs, by the last test."""

import os
import shutil
import struct

import numpy as np
import pytest

from src.modules.core.session import AnalysisSession
from src.modules.data_io.chirascan_reader import ChirascanFormatError, csv_kind, read_chirascan_csv
from src.modules.data_io.loader import group_twins, read_data_file
from src.modules.data_io.prodata_binary import read_prodata_binary
from src.modules.data_io.spectra import subtract

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV = os.path.join(ROOT, "example", "TT3T-10K00000.csv")
REMARKS = ["#User: Chirascan User", "#Date: 2025/10/02", "#Temperature: 24.95 C", "#Cell type: Stopped Flow",
           "#Pathlength: 10"]


def _strings(items):
    return struct.pack("<i", len(items)) + b"".join(s.encode("latin-1") + b"\x00" for s in items)


def write_dsx(path, dims, data, properties=("CircularDichroism", "HV"), remarks=REMARKS):
    """dims: [(name, options, axis)], data: {property: array shaped like reversed dims}."""
    out = b"ProBinaryX\n" + b"Thu Oct 02 15:17:51 2025\x00" + b"\x00\x01{66FEA2B3-CF30-494a-AA87-2}\x00\x07\x00"
    out += _strings(remarks) + _strings(["Misc_AutoShutter:1"])
    out += _strings([f"{p} -autopm" for p in properties])
    out += struct.pack("<i", len(dims))
    for name, opts, axis in dims:
        out += f"{name} {opts}".encode() + b"\x00" + struct.pack("<i", len(axis))
        out += np.asarray(axis, "<f4").tobytes()
    block = b"".join(np.asarray(data[p], "<f4").ravel().tobytes() for p in properties)
    out += struct.pack("<i", len(block)) + block + b"History: ...\x00"
    with open(path, "wb") as f:
        f.write(out)
    return path


def kinetics_dsx(path, n_rep=3, zero_rep=True):
    t = np.round(np.arange(1, 201) * 0.05, 2)
    cd = np.array([4 + 10 * (1 - np.exp(-t / (2 + r))) for r in range(n_rep)])
    if zero_rep:
        cd = np.vstack([cd, np.zeros_like(t)])            # an unused repeat (all zeros)
    hv = np.full_like(cd, 600.0)
    dims = [("Time", "-ovs -trigger", t), ("Wavelength", "-en 3.000000 -ex 3.000000 -iter", [265.0]),
            ("Repeat", "-triggered -iter", np.arange(cd.shape[0]))]
    # reversed dims: [repeat, wavelength, time]
    return write_dsx(path, dims, {"CircularDichroism": cd[:, None, :], "HV": hv[:, None, :]}), t, cd


def spectrum_arrays(offset=0.0):
    wl = np.arange(330, 209.5, -0.5)
    cd = 20 * np.exp(-((wl - 264) / 12) ** 2) - 6 * np.exp(-((wl - 240) / 6) ** 2) + offset
    hv = 400 + 600 * np.exp(-((wl - 255) / 1.2) ** 2)    # saturated detector near 255 nm
    return wl, cd, hv


def spectrum_dsx(path, offset=0.0):
    wl, cd, hv = spectrum_arrays(offset)
    write_dsx(path, [("Wavelength", "-en 3.000000 -ex 3.000000 -iter -range", wl)],
              {"CircularDichroism": cd, "HV": hv})
    return path


def spectrum_csv(path, offset=0.0):
    wl, cd, hv = spectrum_arrays(offset)
    lines = ["ProDataCSV", "", "Title: Thu Oct 02 15:17:51 2025", "", "Remarks:"] + REMARKS + [
        "", "Available Dimensions:,1", "Wavelength,Wavelength: 210nm - 330nm, Step Size: 0.5nm,Bandwidth: 3nm", "",
        "Available Properties: ,2", "CircularDichroism,", "HV,HV", "", "Data:", ""]
    for name, v in (("CircularDichroism", cd), ("HV", hv)):
        lines += ["Wavelength,", name] + [f"{x:g},{y:.6g}" for x, y in zip(wl, v)] + [""]
    lines += ["History: ", "User : Chirascan User"]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


# ---------------------------------------------------------------- reader
def test_binary_kinetics(tmp_path):
    path, t, cd = kinetics_dsx(str(tmp_path / "run00000.dsx"))
    pb = read_prodata_binary(path)
    assert pb.kind == "kinetics" and pb.properties == ["CircularDichroism", "HV"]
    np.testing.assert_allclose(pb.dimension("Time"), t)
    assert pb.dimension("Time")[1] == 0.1                  # float32 values come back as their decimal text
    kind, kf = read_data_file(path)
    assert kind == "kinetics" and kf.fmt == "dsx"
    assert kf.traces == ["CD kinetics 1", "CD kinetics 2", "CD kinetics 3"]   # zero repeat dropped
    np.testing.assert_allclose(kf.data["CD kinetics 2"], cd[1], rtol=1e-6)
    md = kf.metadata
    assert (md["Measurement date"], md["Temperature"], md["Pathlength (mm)"], md["Wavelength (nm)"],
            md["Bandwidth (nm)"]) == ("2025/10/02", "24.95 C", "10", "265", "3")
    assert kf.pathlength_cm == 1.0


def test_damaged_binary_is_reported(tmp_path):
    bad = tmp_path / "broken00000.dsx"
    bad.write_bytes(os.urandom(5000))
    with pytest.raises(ChirascanFormatError, match="damaged"):
        read_data_file(str(bad))
    path, _, _ = kinetics_dsx(str(tmp_path / "cut00000.dsx"))
    raw = open(path, "rb").read()
    with open(path, "wb") as f:
        f.write(raw[:len(raw) // 2])                       # truncated
    with pytest.raises(ChirascanFormatError):
        read_data_file(path)


def test_spectrum_csv_and_dsx_agree(tmp_path):
    k1, s1 = read_data_file(spectrum_csv(str(tmp_path / "sp00000.csv")))
    k2, s2 = read_data_file(spectrum_dsx(str(tmp_path / "sp00000.dsx")))
    assert k1 == k2 == "spectrum"
    assert s1.properties == s2.properties == ["CircularDichroism", "HV"]
    x1, y1 = s1.curve()
    x2, y2 = s2.curve()
    assert x1[0] == 210 and x1[-1] == 330                 # ascending
    np.testing.assert_allclose(x1, x2)
    np.testing.assert_allclose(y1, y2, rtol=1e-4, atol=1e-4)
    assert s1.metadata["Wavelength (nm)"] == s2.metadata["Wavelength (nm)"] == "210–330"
    assert s1.metadata["Bandwidth (nm)"] == s2.metadata["Bandwidth (nm)"] == "3"
    assert s1.metadata["Temperature"] == "24.95 C"


def test_spectrum_csv_is_not_kinetics(tmp_path):
    text = open(spectrum_csv(str(tmp_path / "sp.csv"))).read()
    assert csv_kind(text) == "spectrum"
    assert csv_kind(open(CSV).read()) == "kinetics"
    with pytest.raises(ChirascanFormatError, match="spectrum"):
        read_chirascan_csv(str(tmp_path / "sp.csv"))


def test_hv_limit_and_baseline(tmp_path):
    _, sp = read_data_file(spectrum_dsx(str(tmp_path / "sp.dsx"), offset=0.0))
    _, base = read_data_file(spectrum_dsx(str(tmp_path / "base.dsx"), offset=2.0))
    x, y = sp.curve(hv_max=900)
    hidden = np.isnan(y)
    assert 0 < hidden.sum() < 10 and np.all(np.abs(x[hidden] - 255) < 2)
    assert not np.isnan(sp.curve("HV", hv_max=900)[1]).any()   # HV itself is never hidden
    _, d = subtract(sp.curve(), base.curve())
    np.testing.assert_allclose(d, -2.0, atol=1e-4)


# ---------------------------------------------------------------- session
def test_folder_with_kinetics_spectra_and_twins(tmp_path):
    shutil.copy(CSV, tmp_path / "TT3T 10K00000.csv")
    kinetics_dsx(str(tmp_path / "TT3T 10K00000.dsx"))       # twin of the CSV -> not loaded
    kinetics_dsx(str(tmp_path / "TT3T 10K00001.dsx"), n_rep=2)   # .dsx only
    spectrum_csv(str(tmp_path / "sp TT3T00000.csv"))
    spectrum_dsx(str(tmp_path / "sp TT3T00000.dsx"))
    spectrum_dsx(str(tmp_path / "baseline00000.dsx"), offset=1.0)
    (tmp_path / "broken00000.dsx").write_bytes(b"\x00" * 300)
    from src.modules.data_io.chirascan_reader import data_files_in
    paths = data_files_in(str(tmp_path))
    assert len(group_twins(paths)) == 5
    s = AnalysisSession()
    added, errors = s.add_files(paths)
    assert added == 4 and len(errors) == 1 and "broken00000.dsx" in errors[0]
    assert [f.name for f in s.files] == ["TT3T 10K00000.csv", "TT3T 10K00001.dsx"]
    assert sorted(sp.name for sp in s.spectra) == ["baseline00000.dsx", "sp TT3T00000.csv"]
    assert s.last_added == {"kinetics": 2, "spectra": 2}
    assert s.add_files([str(tmp_path / "TT3T 10K00000.dsx")]) == (0, [])   # twin already loaded


def test_damaged_csv_falls_back_to_dsx(tmp_path):
    (tmp_path / "run00000.csv").write_text("garbage\n1,2\n")
    kinetics_dsx(str(tmp_path / "run00000.dsx"))
    s = AnalysisSession()
    added, errors = s.add_files([str(tmp_path / "run00000.csv"), str(tmp_path / "run00000.dsx")])
    assert added == 1 and errors == [] and s.files[0].fmt == "dsx"


def test_project_keeps_spectra_and_dsx(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    kinetics_dsx(str(data / "run00000.dsx"))
    spectrum_dsx(str(data / "sp00000.dsx"))
    spectrum_csv(str(data / "base00000.csv"), offset=1.0)
    s = AnalysisSession()
    s.add_files(sorted(str(p) for p in data.iterdir()))
    s.spectra[0].visible = False
    s.recompute()
    fp = s.fingerprint
    proj = tmp_path / "p.sfkx"
    s.save_project(str(proj), view_state={"spectrum_baseline": s.spectra[0].path})
    shutil.rmtree(data)                                     # everything comes from the project now
    s2 = AnalysisSession()
    assert s2.load_project(str(proj)) == []
    assert [f.fmt for f in s2.files] == ["dsx"] and s2.fingerprint == fp
    assert [(sp.name, sp.visible) for sp in s2.spectra] == [(sp.name, sp.visible) for sp in s.spectra]
    np.testing.assert_allclose(s2.spectra[1].curve()[1], s.spectra[1].curve()[1])
    assert not s2.has_unsaved_changes


def test_old_project_with_spectrum_as_kinetics(tmp_path):
    """Version 2.0 read a spectrum CSV as kinetics; such a project moves it to the spectra and keeps
    the selection of the real kinetics."""
    sp_path = spectrum_csv(str(tmp_path / "sp00000.csv"))
    s = AnalysisSession()
    s.add_files([CSV])
    state = s.build_state()
    state["files"] = [sp_path, CSV]                         # the spectrum was file 0
    state["embedded_files"] = [{"path": sp_path, "name": "sp00000.csv", "sha1": "x",
                                "content": open(sp_path).read()}] + state["embedded_files"]
    state["settings"]["chosen_columns"] = [[0, "CD kinetics 1"]] + [[1, c] for c in s.files[0].traces[:2]]
    state.pop("spectra", None)
    s2 = AnalysisSession()
    s2.load_state(state)
    assert [f.name for f in s2.files] == ["TT3T-10K00000.csv"]
    assert [sp.name for sp in s2.spectra] == ["sp00000.csv"]
    assert [tuple(c) for c in s2.settings.chosen_columns] == [(0, "CD kinetics 1"), (0, "CD kinetics 2")]
    assert any("is a spectrum" in n for n in s2.load_notes)


def test_excel_sheet_with_spectra(tmp_path):
    pytest.importorskip("xlsxwriter")
    from src.modules.analysis import fitting
    from src.modules.export.excel_export import export_results
    s = AnalysisSession()
    s.add_files([CSV, spectrum_dsx(str(tmp_path / "sp.dsx")), spectrum_dsx(str(tmp_path / "base.dsx"), 1.0)])
    s.recompute()
    k = s.result.kinetics_df
    fit = fitting.fit_model("one phase association", s.specs["one phase association"], k["Time"],
                            k["Average CD kinetics"], check_starts=0, fingerprint=s.fingerprint)
    out = str(tmp_path / "r.xlsx")
    export_results(out, s.files, s.result, fit, include_figures=False,
                   spectra={"items": s.spectra, "prop": "CircularDichroism", "baseline": s.spectra[1],
                            "hv_max": 900.0, "kinetics_wavelengths": [265.0]})
    import openpyxl
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Results", "Spectra"]
    ws = wb["Spectra"]
    assert ws.cell(6, 1).value == "sp.dsx" and ws.cell(7, 1).value == "Wavelength (nm)"
    assert abs(ws.cell(8, 2).value - (-1.0)) < 1e-3          # minus the baseline (offset 1)


@pytest.mark.skipif(not os.environ.get("SFK_DSX_DATA"), reason="SFK_DSX_DATA not set")
def test_real_files_against_their_csv():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from check_dsx_against_csv import main
    assert main([os.environ["SFK_DSX_DATA"]]) == 0
