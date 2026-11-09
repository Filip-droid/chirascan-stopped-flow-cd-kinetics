# tests/test_analysis.py
"""The analysis gives the numbers of the original notebook (reference workbook
example/expected_results_TT3T_10K.xlsx, made by the notebook)."""

import os

import numpy as np
import openpyxl
import pytest

from src.modules.analysis import fitting
from src.modules.core.session import AnalysisSession
from src.modules.export.excel_export import export_results

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLE = os.path.join(ROOT, "example")
CSV = os.path.join(EXAMPLE, "TT3T-10K00000.csv")
REFERENCE = os.path.join(EXAMPLE, "expected_results_TT3T_10K.xlsx")


def reference_values():
    ws = openpyxl.load_workbook(REFERENCE, data_only=True)["Results"]
    out = {}
    for row in ws.iter_rows(min_row=1, max_row=80, max_col=5, values_only=True):
        if row[0] is not None and row[1] is not None:
            out.setdefault(row[0], row[1:])
    return out


@pytest.fixture(scope="module")
def session():
    s = AnalysisSession()
    added, errors = s.add_files([CSV])
    assert added == 1 and not errors
    s.recompute()
    assert s.result is not None, s.processing_error
    return s


def test_loading(session):
    kf = session.files[0]
    assert kf.traces == ["CD kinetics 1", "CD kinetics 2", "CD kinetics 3", "CD kinetics 4"]
    assert len(kf.data) == 5000
    assert kf.metadata["Pathlength (mm)"] == "10"
    assert kf.metadata["Wavelength (nm)"] == "265"
    assert kf.metadata["Bandwidth (nm)"] == "3"


def test_conversion(session):
    ref = reference_values()
    assert session.result.factor == pytest.approx(ref["Conversion factor (mdeg -> delta epsilon)"][0], rel=1e-12)
    assert len(session.result.kinetics_df) == 4999


def test_three_phase_fit_matches_notebook(session):
    spec = session.specs["three phase association"]
    k = session.result.kinetics_df
    r = fitting.fit_model("three phase association", spec, k["Time"], k["Average CD kinetics"],
                          fingerprint=session.fingerprint)
    ref = reference_values()
    for label, value, lo, hi, _ in r["rows"]:
        assert value == pytest.approx(ref[label][0], rel=1e-5), label
        if lo is not None:
            assert lo == pytest.approx(ref[label][1], rel=1e-4), label
    assert r["r_squared"] == pytest.approx(ref["R^2"][0], rel=1e-8)
    assert r["aic"] == pytest.approx(ref["AIC"][0], rel=1e-7)
    assert r["durbin_watson"] == pytest.approx(ref["Durbin-Watson"][0], rel=1e-6)
    session.fits[r["model"]] = r


def test_f_tests_match_notebook(session):
    ref = reference_values()
    k = session.result.kinetics_df
    for name, d in session.f_test_defs.items():
        t = fitting.run_nested_f_test(d["simple"], d["complex"], session.specs, k["Time"],
                                      k["Average CD kinetics"], d["p0_simple"], d["p0_complex"],
                                      fingerprint=session.fingerprint)
        key = f"{d['simple']} vs {d['complex']}"
        assert t["F_stat"] == pytest.approx(ref[key][0], rel=1e-5)
        session.f_tests[name] = t


def test_all_models_fit(session):
    k = session.result.kinetics_df
    for name, spec in session.specs.items():
        r = fitting.fit_model(name, spec, k["Time"], k["Average CD kinetics"], check_starts=0,
                              fingerprint=session.fingerprint)
        assert np.isfinite(r["ss_res"])


def test_export(session, tmp_path):
    out = tmp_path / "results.xlsx"
    export_results(str(out), session.files, session.result, session.fits["three phase association"],
                   session.f_tests.values())
    ws = openpyxl.load_workbook(out)["Results"]
    assert ws["A1"].value == "Stopped-flow CD kinetic analysis"


def test_project_roundtrip(session, tmp_path):
    p = tmp_path / "p.sfkx"
    session.specs["one phase association"]["p0"] = [31.0, 0.2, 26.0]
    session.save_project(str(p))
    s2 = AnalysisSession()
    assert s2.load_project(str(p)) == []
    assert s2.specs["one phase association"]["p0"] == [31.0, 0.2, 26.0]
    assert s2.result.fingerprint == session.result.fingerprint
    # fits, F-tests and the report come back, numerically identical and current
    assert set(s2.fits) == set(session.fits) and set(s2.f_tests) == set(session.f_tests)
    a, b = session.fits["three phase association"], s2.fits["three phase association"]
    assert s2.is_current(b)
    assert np.array_equal(a["params"], b["params"]) and np.array_equal(a["fitted"], b["fitted"])
    assert b["rows"][0][0] == "y0" and b["r_squared"] == a["r_squared"]
    assert s2.f_tests["2 vs 3 exponentials"]["F_stat"] == session.f_tests["2 vs 3 exponentials"]["F_stat"]
    assert not s2.has_unsaved_changes
    s2.specs["one phase association"]["p0"] = [1.0, 0.2, 26.0]
    assert s2.has_unsaved_changes
    # the restored fit can be exported
    export_results(str(tmp_path / "r.xlsx"), s2.files, s2.result, b, s2.f_tests.values())
