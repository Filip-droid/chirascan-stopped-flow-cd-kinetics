# src/modules/analysis/models.py
"""The five exponential models of the notebook and their specifications
(parameter names, initial guesses p0, bounds, plot titles).

Lower bounds: amplitudes and rate constants >= 0; offsets (y0 / asymptote)
are unbounded (only the rate constant k is bounded in the one-phase decay).
Fits can be sensitive to p0; the GUI lets the user edit p0 and the bounds of
every model (default_specs() gives the notebook values back)."""

import copy

import numpy as np


def one_phase_association(t, A, k, y0):
    """Single exponential rise: A*(1-exp(-k*t)) + y0."""
    return A * (1 - np.exp(-k * t)) + y0


def two_phase_association(t, A1, k1, A2, k2, y0):
    """Sum of two exponential rises: A1*(1-exp(-k1*t)) + A2*(1-exp(-k2*t)) + y0."""
    return A1 * (1 - np.exp(-k1 * t)) + A2 * (1 - np.exp(-k2 * t)) + y0


def three_phase_association(t, A1, k1, A2, k2, A3, k3, y0):
    """Sum of three exponential rises plus offset y0."""
    return A1 * (1 - np.exp(-k1 * t)) + A2 * (1 - np.exp(-k2 * t)) + A3 * (1 - np.exp(-k3 * t)) + y0


def one_phase_decay(t, y0, asymptota, k):
    """Single exponential decay: (y0 - asymptota)*exp(-k*t) + asymptota."""
    return (y0 - asymptota) * np.exp(-k * t) + asymptota


def two_phase_decay(t, A1, k1, A2, k2, asymptota):
    """Sum of two exponential decays plus asymptote: A1*exp(-k1*t) + A2*exp(-k2*t) + asymptota."""
    return A1 * np.exp(-k1 * t) + A2 * np.exp(-k2 * t) + asymptota


DELTA_EPS = r"$\Delta\varepsilon$ (M⁻¹cm⁻¹)"
DELTA_EPS_BASES = {"strand": "per strand (whole sequence)", "nucleotide": "per nucleotide"}


def delta_eps_label(basis="strand"):
    """Axis label of Δε for the chosen basis."""
    if basis == "nucleotide":
        return r"$\Delta\varepsilon$ (M⁻¹cm⁻¹ per nucleotide)"
    return r"$\Delta\varepsilon$ (M⁻¹cm⁻¹ per strand)"

# Equations as shown in the GUI (plain text)
EQUATIONS = {
    "one phase association": "y = A·(1 − e^(−k·t)) + y0",
    "two phase association": "y = A1·(1 − e^(−k1·t)) + A2·(1 − e^(−k2·t)) + y0",
    "three phase association": "y = A1·(1 − e^(−k1·t)) + A2·(1 − e^(−k2·t)) + A3·(1 − e^(−k3·t)) + y0",
    "one phase decay": "y = (y0 − asymptota)·e^(−k·t) + asymptota",
    "two phase decay": "y = A1·e^(−k1·t) + A2·e^(−k2·t) + asymptota",
}

_DEFAULT_MODELS = {
    "one phase association": dict(
        func=one_phase_association, names=["A", "k", "y0"], amplitudes=["A"], rates=["k"], kind="association",
        p0=[30, 0.1, 25], lower=[0, 0, -np.inf], upper=[np.inf, np.inf, np.inf],
        fit_title="CD folding kinetics - one exponential model",
        res_title="Residuals analysis - one exponential model"),
    "two phase association": dict(
        func=two_phase_association, names=["A1", "k1", "A2", "k2", "y0"], amplitudes=["A1", "A2"],
        rates=["k1", "k2"], kind="association",
        p0=[700, 0.6, 30, 0.05, 25], lower=[0, 0, 0, 0, -np.inf], upper=[np.inf] * 5,
        fit_title="CD folding kinetics - two exponential model",
        res_title="Residuals analysis - two exponential model"),
    "three phase association": dict(
        func=three_phase_association, names=["A1", "k1", "A2", "k2", "A3", "k3", "y0"],
        amplitudes=["A1", "A2", "A3"], rates=["k1", "k2", "k3"], kind="association",
        p0=[100, 0.08, 50, 0.02, 20, 0.005, 70], lower=[0, 0, 0, 0, 0, 0, -np.inf], upper=[np.inf] * 7,
        fit_title="CD folding kinetics - three exponential model",
        res_title="Residuals analysis - three exponential model"),
    "one phase decay": dict(
        func=one_phase_decay, names=["y0", "asymptota", "k"], amplitudes=[], rates=["k"], kind="decay_one",
        p0=[20, 100, 0.003], lower=[-np.inf, -np.inf, 0], upper=[np.inf, np.inf, np.inf],
        fit_title="CD folding kinetics - one exponential decay",
        res_title="Residuals analysis - one exponential decay"),
    "two phase decay": dict(
        func=two_phase_decay, names=["A1", "k1", "A2", "k2", "asymptota"], amplitudes=["A1", "A2"],
        rates=["k1", "k2"], kind="decay_two",
        p0=[10, 0.1, 5, 0.005, 30], lower=[0, 0, 0, 0, -np.inf], upper=[np.inf] * 5,
        fit_title="Fit of averaged CD kinetics - two phase decay",
        res_title="Residuals analysis - two phase decay"),
}

MODEL_NAMES = list(_DEFAULT_MODELS)

# Nested comparisons of section 6 with the starting values of the original analysis
# (they differ from the p0 of the models).
F_TESTS = {
    "1 vs 2 exponentials": dict(
        simple="one phase association", complex="two phase association",
        p0_simple=[30, 0.1, 25], p0_complex=[20, 0.1, 100, 0.05, 25], short=("Single", "Two")),
    "2 vs 3 exponentials": dict(
        simple="two phase association", complex="three phase association",
        p0_simple=[20, 0.01, 10, 0.005, 25], p0_complex=[100, 0.150, 50, 0.02, 20, 0.005, 70],
        short=("Two", "Three")),
}


for _spec in _DEFAULT_MODELS.values():
    _spec["fixed"] = [False] * len(_spec["names"])     # parameters held at p0 during the fit


def default_specs():
    """A fresh, editable copy of the model specifications."""
    return copy.deepcopy(_DEFAULT_MODELS)


def default_f_tests():
    return copy.deepcopy(F_TESTS)
