# src/modules/analysis/fitting.py
"""Sections 4-6 of the notebook: fitting of one model (parameters with 95 %
confidence intervals, τ and half-lives, goodness of fit, residual
autocorrelation, multi-start check, sanity warnings) and the extra-sum-of-
squares F-test of nested models. No GUI code here: the functions take arrays
and return plain dictionaries.

Parameters can be fixed (spec["fixed"], a bool per parameter): they keep
their p0 value, only the free ones are fitted, and the statistics count only
the free parameters (degrees of freedom, AIC, BIC). Fixed parameters have no
confidence interval. The F-tests always fit all parameters."""

import warnings

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter

DEFAULT_CHECK_STARTS = 5
DEFAULT_SAVGOL_WINDOW = 51
DEFAULT_SAVGOL_ORDER = 3


class FitError(RuntimeError):
    pass


def fixed_flags(spec):
    """[bool] per parameter: True = fixed at its p0."""
    flags = spec.get("fixed") or []
    return [bool(f) for f in flags] + [False] * (len(spec["names"]) - len(flags))


def _curve_fit(func, x_data, y_data, p0, lower, upper, fixed=None):
    """curve_fit with some parameters held at their p0. Returns the full parameter vector and a
    full covariance matrix (zero rows/columns for the fixed parameters)."""
    p0 = np.asarray(p0, dtype=float)
    fixed = np.asarray(fixed if fixed is not None else [False] * len(p0), dtype=bool)
    if not fixed.any():
        return curve_fit(func, x_data, y_data, p0=p0, bounds=(lower, upper), maxfev=10000)
    free = np.flatnonzero(~fixed)
    if free.size == 0:
        raise ValueError("all parameters are fixed - free at least one")

    def reduced(t, *q):
        full = p0.copy()
        full[free] = q
        return func(t, *full)

    lo = np.asarray(lower, dtype=float)[free]
    hi = np.asarray(upper, dtype=float)[free]
    q, cov_free = curve_fit(reduced, x_data, y_data, p0=p0[free], bounds=(lo, hi), maxfev=10000)
    params = p0.copy()
    params[free] = q
    cov = np.zeros((len(p0), len(p0)))
    cov[np.ix_(free, free)] = cov_free
    return params, cov


def fit_curve(func, x_data, y_data, p0, lower, upper, label, fixed=None):
    """curve_fit wrapper with a readable error message (and optionally fixed parameters)."""
    try:
        return _curve_fit(func, x_data, y_data, p0, lower, upper, fixed)
    except (RuntimeError, ValueError) as exc:
        raise FitError(
            f"{label} fit failed (no convergence or invalid input). Try different initial guesses (p0) "
            f"or bounds. Original error: {exc}") from exc


def multistart_check(spec, x_data, y_data, ss_res_main, n_starts, seed=0):
    """Refit from randomly perturbed p0 (log-normal, sigma = 0.5; fixed parameters stay) and report
    whether a lower minimum exists."""
    if n_starts <= 0:
        return "not performed"
    rng = np.random.default_rng(seed)
    p0 = np.asarray(spec["p0"], dtype=float)
    fixed = np.asarray(fixed_flags(spec))
    ss_list = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(n_starts):
            trial = np.clip(p0 * np.exp(rng.normal(0.0, 0.5, size=p0.size)), spec["lower"], spec["upper"])
            trial[fixed] = p0[fixed]
            try:
                trial_params, _ = _curve_fit(spec["func"], x_data, y_data, trial, spec["lower"], spec["upper"],
                                             fixed)
            except (RuntimeError, ValueError):
                continue
            ss_list.append(np.sum((y_data - spec["func"](x_data, *trial_params)) ** 2))
    if not ss_list:
        return f"0/{n_starts} perturbed starts converged - the fit may be very sensitive to p0"
    ss_arr = np.array(ss_list)
    same = int(np.sum(np.abs(ss_arr - ss_res_main) <= 1e-6 * ss_res_main))
    text = f"{len(ss_arr)}/{n_starts} perturbed starts converged, {same} reached the same minimum"
    if ss_arr.min() < ss_res_main * (1 - 1e-6):
        text += (f"; WARNING: a LOWER minimum was found (SSR {ss_arr.min():.6g} vs {ss_res_main:.6g}) - "
                 f"consider changing p0 for this model")
    else:
        text += "; no lower minimum found"
    return text


def quality_warnings(spec, params, cis, covariance):
    """Simple sanity checks of a fit; returns a list of warning strings."""
    found = []
    fixed = fixed_flags(spec)
    if not np.all(np.isfinite(covariance)):
        found.append("covariance matrix is not finite - confidence intervals are undefined "
                     "(poorly determined parameters)")
    for i, name in enumerate(spec["names"]):
        if fixed[i]:
            continue
        lower = spec["lower"][i]
        if np.isfinite(lower) and abs(params[i] - lower) < 1e-8:
            found.append(f"{name} is at its lower bound ({lower}) - the phase may not be present in the data")
    for name in spec["rates"]:
        i = spec["names"].index(name)
        if fixed[i]:
            continue
        if np.isfinite(cis[0][i]) and cis[0][i] <= 0:
            found.append(f"95 % CI of {name} includes zero - the rate constant is poorly determined")
    return found


def smooth_residuals(residuals, window=DEFAULT_SAVGOL_WINDOW, order=DEFAULT_SAVGOL_ORDER):
    """Savitzky-Golay smoothed residuals (the window is shrunk for short data)."""
    n = len(residuals)
    w = min(int(window), n if n % 2 else n - 1)
    if w % 2 == 0:
        w -= 1
    if w <= order:
        return None
    return savgol_filter(residuals, window_length=w, polyorder=order)


def _equation(spec, par):
    def add(v):
        return f"+ {v:.4f}" if v >= 0 else f"- {abs(v):.4f}"

    def sub(v):
        return f"- {v:.4f}" if v >= 0 else f"+ {abs(v):.4f}"

    if spec["kind"] == "association":
        terms = " + ".join(f"{par[a]:.4f} * (1 - exp(-{par[r]:.4f} * t))"
                           for a, r in zip(spec["amplitudes"], spec["rates"]))
        return f"y = {terms} {add(par['y0'])}"
    if spec["kind"] == "decay_one":
        return f"y = ({par['y0']:.4f} {sub(par['asymptota'])}) * exp(-{par['k']:.4f} * t) {add(par['asymptota'])}"
    terms = " + ".join(f"{par[a]:.4f} * exp(-{par[r]:.4f} * t)" for a, r in zip(spec["amplitudes"], spec["rates"]))
    return f"y = {terms} {add(par['asymptota'])}"


def fit_model(model_name, spec, x_data, y_data, check_starts=DEFAULT_CHECK_STARTS,
              savgol_window=DEFAULT_SAVGOL_WINDOW, fingerprint=None, y_label=None):
    """Fit one model; returns the result dictionary of the notebook's fit_model()."""
    func = spec["func"]
    names = spec["names"]
    x_data = np.asarray(x_data, dtype=float)
    y_data = np.asarray(y_data, dtype=float)

    fixed = fixed_flags(spec)
    fixed_names = [n_ for n_, f in zip(names, fixed) if f]
    if all(fixed):
        raise FitError(f"{model_name.capitalize()}: all parameters are fixed - free at least one.")
    params, covariance = fit_curve(func, x_data, y_data, spec["p0"], spec["lower"], spec["upper"],
                                   model_name.capitalize(), fixed=fixed)
    par = dict(zip(names, params))

    # 95 % confidence intervals (t-distribution, from the covariance matrix); fixed parameters have none
    alpha = 0.05
    n = len(y_data)
    p = len(params) - len(fixed_names)          # free parameters
    dof = max(0, n - p)
    t_val = stats.t.ppf(1.0 - alpha / 2.0, dof)
    with np.errstate(invalid="ignore"):
        std_errs = np.sqrt(np.diag(covariance))
    cis = [params - t_val * std_errs, params + t_val * std_errs]
    for i, f in enumerate(fixed):
        if f:
            cis[0][i] = cis[1][i] = np.nan
    ci = {name: (cis[0][i], cis[1][i]) for i, name in enumerate(names)}

    # Tau (1/k) and half-life (ln2/k); their CIs follow from the CI of k
    tau, half_life, tau_ci, half_life_ci = {}, {}, {}, {}
    for r in spec["rates"]:
        k = par[r]
        with np.errstate(divide="ignore"):
            tau[r] = 1 / k if k != 0 else np.inf
            half_life[r] = np.log(2) / k if k != 0 else np.inf
        k_lo, k_hi = ci[r]
        if np.isfinite(k_lo) and np.isfinite(k_hi) and k_lo > 0:
            tau_ci[r] = (1 / k_hi, 1 / k_lo)
            half_life_ci[r] = (np.log(2) / k_hi, np.log(2) / k_lo)
        else:
            tau_ci[r] = half_life_ci[r] = None

    # y0 and asymptote (value at t -> infinity)
    if spec["kind"] == "association":
        y0, y0_ci = par["y0"], ci["y0"]
        asymptote = sum([par[a] for a in spec["amplitudes"]] + [y0])
        asymptote_ci = None
    elif spec["kind"] == "decay_one":
        y0, y0_ci = par["y0"], ci["y0"]
        asymptote, asymptote_ci = par["asymptota"], ci["asymptota"]
    else:  # decay_two: y0 = f(0), SE by the delta method
        y0 = func(0, *params)
        derivatives = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
        se_y0 = np.sqrt(derivatives @ covariance @ derivatives.T)
        y0_ci = (y0 - t_val * se_y0, y0 + t_val * se_y0)
        asymptote, asymptote_ci = par["asymptota"], ci["asymptota"]

    fitted = func(x_data, *params)
    residuals = y_data - fitted

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    rmsd = np.sqrt(ss_res / n)
    aic = n * np.log(ss_res / n) + 2 * p
    bic = n * np.log(ss_res / n) + p * np.log(n)
    sigma2_hat = ss_res / (n - p)
    log_likelihood = -0.5 * n * np.log(2 * np.pi * sigma2_hat) - (ss_res / (2 * sigma2_hat))
    aic2 = -2 * log_likelihood + 2 * p
    bic2 = -2 * log_likelihood + p * np.log(n)
    durbin_watson = np.sum(np.diff(residuals) ** 2) / np.sum(residuals ** 2)
    lag1_autocorr = np.sum(residuals[1:] * residuals[:-1]) / np.sum(residuals ** 2)

    equation = _equation(spec, par)

    unit_signal = "M^-1 cm^-1"

    def label_of(name):
        return f"{name} (fixed)" if name in fixed_names else name

    def interval(pair):
        return (None, None) if pair is None or not np.all(np.isfinite(pair)) else pair

    rows = [(label_of("y0"), y0, *interval(y0_ci), unit_signal)]
    for a in spec["amplitudes"]:
        rows.append((label_of(a), par[a], *interval(ci[a]), unit_signal))
    for r in spec["rates"]:
        rows.append((label_of(r), par[r], *interval(ci[r]), "s^-1"))
    rows.append(("Asymptote (fixed)" if "asymptota" in fixed_names else "Asymptote", asymptote,
                 *interval(asymptote_ci), unit_signal))
    for r in spec["rates"]:
        suffix = r[1:]
        for label, value, interval in (("Tau" + suffix, tau[r], tau_ci[r]),
                                       ("Half Life" + suffix, half_life[r], half_life_ci[r])):
            rows.append((label, value, *(interval if interval else (None, None)), "s"))

    found = quality_warnings(spec, params, cis, covariance)
    multistart = multistart_check(spec, x_data, y_data, ss_res, check_starts)
    smoothed = smooth_residuals(residuals, savgol_window)

    return dict(
        model=model_name, names=names, params=params, covariance=covariance, cis=cis, par=par, ci=ci,
        tau=tau, half_life=half_life, tau_ci=tau_ci, half_life_ci=half_life_ci,
        y0=y0, y0_ci=y0_ci, asymptote=asymptote, asymptote_ci=asymptote_ci,
        x=x_data, y=y_data, residuals=residuals, smoothed_residuals=smoothed, fitted=fitted,
        ss_res=ss_res, r_squared=r_squared, rmsd=rmsd, aic=aic, bic=bic, aic2=aic2, bic2=bic2,
        durbin_watson=durbin_watson, lag1_autocorr=lag1_autocorr, n_points=n, n_params=p,
        equation=equation, rows=rows, warnings=found, multistart=multistart,
        p0_used=list(spec["p0"]), fixed=fixed_names, data_fingerprint=fingerprint,
        fit_title=spec.get("fit_title", model_name), res_title=spec.get("res_title", "Residuals"),
        y_label=y_label,
    )


def format_result_text(result):
    """The printed report of the notebook's fit_model()."""
    lines = [f"=== {result['model']} ==="]
    if result.get("fixed"):
        lines.append("Fixed (not fitted): " + ", ".join(
            f"{n} = {result['par'][n]:.6g}" for n in result["fixed"]))
    for label, value, lo, hi, unit in result["rows"]:
        fmt = ".5f" if unit == "s^-1" else ".3f"
        if lo is None:
            lines.append(f"{label} = {value:{fmt}} {unit}")
        else:
            lines.append(f"{label} = {value:{fmt}} ({lo:{fmt}}, {hi:{fmt}}) {unit}")
    lines += ["",
              f"R^2: {result['r_squared']:.3f}",
              f"RMSD: {result['rmsd']:.3f}",
              f"AIC: {result['aic']:.3f}",
              f"BIC: {result['bic']:.3f}",
              f"AIC (Gaussian log-likelihood): {result['aic2']:.3f}",
              f"BIC (Gaussian log-likelihood): {result['bic2']:.3f}",
              f"Durbin-Watson: {result['durbin_watson']:.3f} "
              f"(lag-1 residual autocorrelation: {result['lag1_autocorr']:.3f})",
              "", f"{result['model'].capitalize()} equation:", result["equation"], "",
              f"Multi-start check: {result['multistart']}"]
    lines += [f"WARNING: {m}" for m in result["warnings"]]
    return "\n".join(lines)


def run_nested_f_test(simple, complex_, specs, x_data, y_data, p0_simple, p0_complex, fingerprint=None,
                      y_label=None):
    """Extra-sum-of-squares F-test of a simpler model against a more complex one that contains it."""
    x_data = np.asarray(x_data, dtype=float)
    y_data = np.asarray(y_data, dtype=float)
    fits = {}
    for name, p0 in ((simple, p0_simple), (complex_, p0_complex)):
        spec = specs[name]
        params, _ = fit_curve(spec["func"], x_data, y_data, p0, spec["lower"], spec["upper"], name.capitalize())
        residuals = y_data - spec["func"](x_data, *params)
        fits[name] = dict(params=params, residuals=residuals, ss_res=np.sum(residuals ** 2),
                          n_params=len(params), fitted=spec["func"](x_data, *params))
    n = len(y_data)
    s, c = fits[simple], fits[complex_]
    df_res_simple = n - s["n_params"]
    df_res_complex = n - c["n_params"]
    df_num = c["n_params"] - s["n_params"]
    F_stat = ((s["ss_res"] - c["ss_res"]) / df_num) / (c["ss_res"] / df_res_complex)
    p_value = stats.f.sf(F_stat, df_num, df_res_complex)
    return dict(simple=simple, complex=complex_, F_stat=F_stat, p_value=p_value,
                df_numerator=df_num, df_residual=df_res_complex, df_residual_simple=df_res_simple,
                ss_res_simple=s["ss_res"], ss_res_complex=c["ss_res"],
                x=x_data, y=y_data, fit_simple=s, fit_complex=c, data_fingerprint=fingerprint, y_label=y_label)


def format_f_test_text(t, alpha=0.05):
    p = t["p_value"]
    p_txt = "< 1e-300 (underflow)" if p == 0 else f"{p:.4g}"
    verdict = (f"The more complex model ({t['complex']}) improves the fit significantly (p < {alpha})."
               if p < alpha else
               f"The more complex model does not improve the fit significantly (p ≥ {alpha}); "
               f"prefer {t['simple']}.")
    return "\n".join([
        f"=== {t['simple']} vs {t['complex']} ===",
        f"SS_res ({t['simple']}): {t['ss_res_simple']:.6g}",
        f"SS_res ({t['complex']}): {t['ss_res_complex']:.6g}",
        f"Degrees of freedom ({t['simple']}): {t['df_residual_simple']}",
        f"Degrees of freedom ({t['complex']}): {t['df_residual']}",
        f"F-statistic: {t['F_stat']:.6g}  (df = {t['df_numerator']}, {t['df_residual']})",
        f"P-value: {p_txt}",
        verdict,
    ])
