# tests/test_fixed_and_p0.py
"""Fixed parameters during the fit and the estimate of p0 from the data."""

import os

import numpy as np
import pytest

from src.modules.analysis import fitting
from src.modules.analysis.initial_guess import estimate_p0, heuristic_p0
from src.modules.analysis.models import default_specs
from src.modules.core.session import AnalysisSession

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV = os.path.join(ROOT, "example", "TT3T-10K00000.csv")
TRUE_2 = [60.0, 0.17, 110.0, 0.018, 70.0]          # A1, k1, A2, k2, y0


def two_phase_data(noise=2.0, seed=1):
    t = np.round(np.arange(1, 5001) * 0.1, 1)
    y = default_specs()["two phase association"]["func"](t, *TRUE_2)
    return t, y + np.random.default_rng(seed).normal(0, noise, t.size)


def ssr(spec, x, y, p):
    return float(np.sum((y - spec["func"](x, *p)) ** 2))


def test_estimate_starts_at_the_minimum():
    x, y = two_phase_data()
    spec = default_specs()["two phase association"]
    p0 = estimate_p0(spec, x, y)
    np.testing.assert_allclose(p0, TRUE_2, rtol=0.1)
    fit = fitting.fit_model("two phase association", dict(spec, p0=p0), x, y, check_starts=0)
    assert ssr(spec, x, y, p0) < 1.02 * fit["ss_res"]
    assert ssr(spec, x, y, heuristic_p0(spec, x, y)) > ssr(spec, x, y, p0)    # better than v2.0


@pytest.mark.parametrize("model", list(default_specs()))
def test_estimate_on_the_example_is_close_to_the_fit(model):
    s = AnalysisSession()
    s.add_files([CSV])
    s.recompute()
    k = s.result.kinetics_df
    x, y = k["Time"].values, k["Average CD kinetics"].values
    spec = s.specs[model]
    p0 = estimate_p0(spec, x, y)
    assert all(lo <= v <= hi for v, lo, hi in zip(p0, spec["lower"], spec["upper"]))
    fit = fitting.fit_model(model, dict(spec, p0=p0), x, y, check_starts=3)
    assert ssr(spec, x, y, p0) < 1.05 * fit["ss_res"]
    assert "LOWER" not in fit["multistart"]


def test_fixed_parameter_is_kept_and_not_counted():
    x, y = two_phase_data()
    spec = default_specs()["two phase association"]
    spec["p0"] = [50, 0.1, 100, 0.018, 60]
    spec["fixed"] = [False, False, False, True, False]          # k2 fixed at 0.018
    fit = fitting.fit_model("two phase association", spec, x, y, check_starts=3)
    assert fit["par"]["k2"] == 0.018 and fit["fixed"] == ["k2"]
    assert fit["n_params"] == 4
    np.testing.assert_allclose(fit["params"], TRUE_2, rtol=0.05)
    rows = {r[0]: r for r in fit["rows"]}
    assert rows["k2 (fixed)"][2] is None and rows["k1"][2] is not None
    assert fit["tau_ci"]["k2"] is None
    assert np.all(fit["covariance"][3] == 0)
    assert "Fixed (not fitted): k2 = 0.018" in fitting.format_result_text(fit)
    # AIC uses the 4 fitted parameters
    n = len(y)
    assert fit["aic"] == pytest.approx(n * np.log(fit["ss_res"] / n) + 2 * 4)


def test_fixed_level_of_a_decay():
    t = np.linspace(0.1, 300, 2000)
    y = (120 - 40) * np.exp(-0.02 * t) + 40 + np.random.default_rng(3).normal(0, 1, t.size)
    spec = default_specs()["one phase decay"]
    spec["p0"] = [100, 45, 0.01]
    spec["fixed"] = [False, True, False]                       # asymptota = 45 (not the true 40)
    p0 = estimate_p0(spec, t, y)
    assert p0[1] == 45
    fit = fitting.fit_model("one phase decay", dict(spec, p0=p0), t, y, check_starts=2)
    assert fit["par"]["asymptota"] == 45 and fit["n_params"] == 2
    assert any(r[0] == "Asymptote (fixed)" for r in fit["rows"])


def test_estimate_respects_a_fixed_rate():
    x, y = two_phase_data()
    spec = default_specs()["two phase association"]
    spec["p0"] = [1, 1, 1, 0.05, 1]
    spec["fixed"] = [False, False, False, True, False]
    p0 = estimate_p0(spec, x, y)
    assert p0[3] == 0.05


def test_all_fixed_is_refused():
    x, y = two_phase_data()
    spec = default_specs()["one phase association"]
    spec["fixed"] = [True, True, True]
    with pytest.raises(fitting.FitError, match="all parameters are fixed"):
        fitting.fit_model("one phase association", spec, x, y)


def test_project_keeps_fixed_parameters(tmp_path):
    s = AnalysisSession()
    s.add_files([CSV])
    s.specs["two phase association"]["fixed"] = [False, True, False, False, False]
    p = tmp_path / "p.sfkx"
    s.save_project(str(p))
    s2 = AnalysisSession()
    s2.load_project(str(p))
    assert s2.specs["two phase association"]["fixed"] == [False, True, False, False, False]
    assert s2.specs["one phase association"]["fixed"] == [False, False, False]
