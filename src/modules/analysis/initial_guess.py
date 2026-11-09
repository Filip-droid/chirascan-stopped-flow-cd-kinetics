# src/modules/analysis/initial_guess.py
"""Estimate p0 of a model from the data (button "Estimate p0"): the start and
end level of the (smoothed) trace and the times at which the signal covers a
given fraction of its change; a rate constant is ln 2 / that time. Only a
starting point for the fit - not a result."""

import numpy as np


def _level_times(x, y, fractions):
    n = len(y)
    w = max(3, n // 50)
    kernel = np.ones(w) / w
    ys = np.convolve(y, kernel, mode="same") if n > 2 * w else y
    head = max(3, n // 100)
    tail = max(3, n // 20)
    y_start = float(np.median(y[:head]))
    y_end = float(np.median(y[-tail:]))
    delta = y_end - y_start
    times = []
    for f in fractions:
        target = y_start + f * delta
        reached = np.nonzero((ys - target) * np.sign(delta or 1) >= 0)[0]
        t = x[reached[0]] if reached.size else x[n // 2]
        times.append(max(float(t), float(x[1] - x[0]) if n > 1 else 1e-3, 1e-9))
    return y_start, y_end, delta, times


def estimate_p0(spec, x, y):
    """p0 for the model `spec` (same order as spec['names'])."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ln2 = np.log(2)
    kind, names = spec["kind"], spec["names"]
    n_phase = len(spec["rates"])
    fractions = {1: [0.5], 2: [0.25, 0.75], 3: [0.15, 0.5, 0.85]}[n_phase]
    shares = {1: [1.0], 2: [0.5, 0.5], 3: [0.35, 0.35, 0.3]}[n_phase]
    y_start, y_end, delta, times = _level_times(x, y, fractions)
    ks = [ln2 / t for t in times]
    values = {}
    if kind == "association":
        values["y0"] = y_start
        for a, r, s, k in zip(spec["amplitudes"], spec["rates"], shares, ks):
            values[a] = abs(delta) * s
            values[r] = k
    elif kind == "decay_one":
        values.update(y0=y_start, asymptota=y_end, k=ks[0])
    else:
        values["asymptota"] = y_end
        for a, r, s, k in zip(spec["amplitudes"], spec["rates"], shares, ks):
            values[a] = abs(delta) * s
            values[r] = k
    p0 = []
    for i, name in enumerate(names):
        v = values[name]
        lo, hi = spec["lower"][i], spec["upper"][i]
        if np.isfinite(lo) and v < lo:
            v = lo
        if np.isfinite(hi) and v > hi:
            v = hi
        p0.append(float(f"{v:.4g}"))
    return p0
