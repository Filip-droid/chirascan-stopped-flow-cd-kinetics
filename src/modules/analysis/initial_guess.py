# src/modules/analysis/initial_guess.py
"""Estimate p0 of a model from the data (button "Estimate p0").

Every model is linear in all its parameters except the rate constants:
for given k's, the amplitudes and the offset follow from a linear least-
squares problem. The estimate therefore

1. averages the trace into at most ~600 points (speed only),
2. tries rate constants on a logarithmic grid (from ~1/(3 x the time span)
   to ~3/(time step), one phase faster than the next) and solves the linear
   parameters exactly for each combination, keeping the best,
3. refines the rate constants from there (Nelder-Mead on log k),
4. clips everything to the bounds and rounds to 4 significant digits.

This "variable projection" search finds the region of the global minimum
also for two and three phases, so the fit starts near it. Fixed parameters
(spec["fixed"]) keep their value and are taken into account. It is only a
starting point for the fit - not a result. If the search fails, the simpler
estimate of earlier versions (levels and times of fractional change) is used."""

import itertools

import numpy as np
from scipy.optimize import lsq_linear, minimize

MAX_POINTS = 600
GRID = {1: 60, 2: 36, 3: 20}          # grid points per rate constant


# ---------------------------------------------------------------- the simple estimate (v2.0)
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


def heuristic_p0(spec, x, y):
    """Start/end level and the times of 25/50/75 % change (ln 2 / t gives k)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    kind = spec["kind"]
    n_phase = len(spec["rates"])
    fractions = {1: [0.5], 2: [0.25, 0.75], 3: [0.15, 0.5, 0.85]}[n_phase]
    shares = {1: [1.0], 2: [0.5, 0.5], 3: [0.35, 0.35, 0.3]}[n_phase]
    y_start, y_end, delta, times = _level_times(x, y, fractions)
    ks = [np.log(2) / t for t in times]
    values = {}
    if kind == "association":
        values["y0"] = y_start
    elif kind == "decay_one":
        values.update(y0=y_start, asymptota=y_end)
    else:
        values["asymptota"] = y_end
    for a, s in zip(spec["amplitudes"], shares):
        values[a] = abs(delta) * s
    for r, k in zip(spec["rates"], ks):
        values[r] = k
    return _finish(spec, values)


# ---------------------------------------------------------------- variable projection
def _basis(spec, name, t, k):
    """The function that multiplies the linear parameter `name` (k: rate constants by name)."""
    kind = spec["kind"]
    if kind == "association":
        if name == "y0":
            return np.ones_like(t)
        r = spec["rates"][spec["amplitudes"].index(name)]
        return 1.0 - np.exp(-k[r] * t)
    if kind == "decay_one":                     # y = y0*e^(-kt) + asymptota*(1 - e^(-kt))
        e = np.exp(-k["k"] * t)
        return e if name == "y0" else 1.0 - e
    if name == "asymptota":                     # decay_two
        return np.ones_like(t)
    r = spec["rates"][spec["amplitudes"].index(name)]
    return np.exp(-k[r] * t)


def _bin(x, y, max_points=MAX_POINTS):
    n = len(x)
    if n <= max_points:
        return x, y
    edges = np.linspace(0, n, max_points + 1).astype(int)
    xb = np.array([x[a:b].mean() for a, b in zip(edges[:-1], edges[1:]) if b > a])
    yb = np.array([y[a:b].mean() for a, b in zip(edges[:-1], edges[1:]) if b > a])
    return xb, yb


class _Projection:
    """SSR(rate constants) with the linear parameters solved (within their bounds)."""

    def __init__(self, spec, x, y, fixed_values):
        self.spec = spec
        self.x, self.y = x, y
        self.fixed = fixed_values                      # name -> value
        names = spec["names"]
        self.linear = [n for n in names if n not in spec["rates"]]
        self.free_linear = [n for n in self.linear if n not in fixed_values]
        self.bounds = ([spec["lower"][names.index(n)] for n in self.free_linear],
                       [spec["upper"][names.index(n)] for n in self.free_linear])

    def solve(self, k):
        """(SSR, {linear parameter: value}) for the rate constants k (dict)."""
        target = self.y.copy()
        for n in self.linear:
            if n in self.fixed:
                target -= self.fixed[n] * _basis(self.spec, n, self.x, k)
        if not self.free_linear:
            return float(np.sum(target ** 2)), {}
        A = np.column_stack([_basis(self.spec, n, self.x, k) for n in self.free_linear])
        theta, *_ = np.linalg.lstsq(A, target, rcond=None)
        lo, hi = map(np.asarray, self.bounds)
        if np.any(theta < lo) or np.any(theta > hi):
            theta = lsq_linear(A, target, bounds=(lo, hi), method="bvls").x
        res = target - A @ theta
        return float(res @ res), dict(zip(self.free_linear, theta))


def _rate_range(spec, x, name):
    span = float(x[-1] - x[0]) if len(x) > 1 else 1.0
    dt = float(np.min(np.diff(x))) if len(x) > 1 else span
    lo = max(0.3 / max(span, 1e-12), 1e-12)
    hi = max(3.0 / max(dt, 1e-12), lo * 10)
    i = spec["names"].index(name)
    l_b, u_b = spec["lower"][i], spec["upper"][i]
    if np.isfinite(l_b) and l_b > 0:
        lo = max(lo, l_b)
    if np.isfinite(u_b):
        hi = min(hi, u_b)
    return lo, max(hi, lo * 1.0001)


def projection_p0(spec, x, y):
    """p0 by variable projection (see the module text). Raises on failure."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < len(spec["names"]) + 2:
        raise ValueError("too few points")
    order = np.argsort(x)
    xb, yb = _bin(x[order], y[order])
    names = spec["names"]
    fixed_flags = spec.get("fixed") or [False] * len(names)
    fixed = {n: float(spec["p0"][i]) for i, n in enumerate(names) if fixed_flags[i]}
    proj = _Projection(spec, xb, yb, {n: v for n, v in fixed.items() if n not in spec["rates"]})
    free_rates = [r for r in spec["rates"] if r not in fixed]
    fixed_rates = {r: fixed[r] for r in spec["rates"] if r in fixed}

    def ssr(log_k):
        k = dict(fixed_rates, **{r: float(np.exp(v)) for r, v in zip(free_rates, log_k)})
        return proj.solve(k)[0]

    if free_rates:
        ranges = [_rate_range(spec, xb, r) for r in free_rates]
        n_grid = GRID[len(free_rates)]
        grids = [np.linspace(np.log(lo), np.log(hi), n_grid) for lo, hi in ranges]
        best, best_lk = np.inf, None
        # the phases are numbered fast -> slow (k1 > k2 > k3), as in the original p0
        for combo in itertools.product(*[range(n_grid)] * len(free_rates)):
            if any(a <= b for a, b in zip(combo, combo[1:])):
                continue
            lk = [g[i] for g, i in zip(grids, combo)]
            v = ssr(lk)
            if v < best:
                best, best_lk = v, lk
        if best_lk is None:
            raise ValueError("no rate constants to try")
        step = (grids[0][1] - grids[0][0]) if n_grid > 1 else 0.5
        simplex = [best_lk] + [list(np.add(best_lk, step * np.eye(len(best_lk))[i])) for i in range(len(best_lk))]
        opt = minimize(ssr, best_lk, method="Nelder-Mead",
                       options={"initial_simplex": simplex, "maxfev": 400, "xatol": 1e-4, "fatol": 1e-10})
        lk = opt.x if opt.fun <= best else best_lk
        k = dict(fixed_rates, **{r: float(np.exp(v)) for r, v in zip(free_rates, lk)})
    else:
        k = dict(fixed_rates)
    _, linear = proj.solve(k)
    values = dict(fixed)
    values.update(k)
    values.update(linear)
    # keep the fast-to-slow numbering
    if len(free_rates) > 1 and spec["amplitudes"]:
        pairs = sorted(((values[r], values[a]) for r, a in zip(spec["rates"], spec["amplitudes"])
                        if r in free_rates and a not in fixed), reverse=True)
        slots = [(r, a) for r, a in zip(spec["rates"], spec["amplitudes"]) if r in free_rates and a not in fixed]
        for (r, a), (kv, av) in zip(slots, pairs):
            values[r], values[a] = kv, av
    return _finish(spec, values)


def _finish(spec, values):
    p0 = []
    fixed_flags = spec.get("fixed") or [False] * len(spec["names"])
    for i, name in enumerate(spec["names"]):
        if fixed_flags[i]:
            p0.append(float(spec["p0"][i]))
            continue
        v = float(values[name])
        lo, hi = spec["lower"][i], spec["upper"][i]
        if np.isfinite(lo) and v < lo:
            v = lo
        if np.isfinite(hi) and v > hi:
            v = hi
        v = float(f"{v:.4g}")
        # a rate constant exactly at a lower bound of 0 would stall the fit
        if name in spec["rates"] and v <= 0 and not (np.isfinite(lo) and lo > 0):
            v = 1e-6
        p0.append(v)
    return p0


def estimate_p0(spec, x, y):
    """p0 for the model `spec` (same order as spec['names']); fixed parameters are kept."""
    try:
        return projection_p0(spec, x, y)
    except (ValueError, np.linalg.LinAlgError, FloatingPointError):
        return heuristic_p0(spec, x, y)
