# src/modules/visualization/figures.py
"""All plots of the program, drawn onto a given matplotlib Figure (the GUI
canvases and the Excel export use the same functions, so what is exported is
what is seen)."""

import io
import os

from matplotlib.figure import Figure

from src.modules.analysis.models import DELTA_EPS
from src.modules.analysis.processing import AVERAGE_COLUMN

MDEG = "CD (mdeg)"
TIME = "Time (s)"


def _finish(ax, title, xlabel=TIME, ylabel=MDEG, legend=True):
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.4)
    if legend and ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=8, loc="best")


def message(fig, text):
    """An empty plot with a grey note in the middle."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, text, ha="center", va="center", color="#888888", fontsize=11, wrap=True,
            transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#DDDDDD")


def raw_traces(fig, files, chosen=None, show_unused=False):
    """CD kinetics of every file: the ticked traces; the unticked ones are hidden
    (or, with show_unused, drawn faint grey and dashed)."""
    fig.clear()
    if not files:
        message(fig, "No data loaded.\nUse File › Open folder… or File › Add CSV files…")
        return
    chosen = set(chosen or [])
    if not chosen and not show_unused:
        message(fig, "No trace is ticked.\nTick the traces to average in 'Traces to average'\n"
                     "(or tick 'Show unticked traces' to see them).")
        return
    n = len(files)
    axes = [fig.add_subplot(n, 1, i + 1) for i in range(n)] if n <= 3 else [fig.add_subplot(111)]
    for idx, kf in enumerate(files):
        ax = axes[idx] if n <= 3 else axes[0]
        for column in kf.traces:
            label = column if n <= 3 else f"{kf.name}: {column}"
            if (idx, column) in chosen:
                ax.plot(kf.data["Time"], kf.data[column], lw=0.9, label=label)
            elif show_unused:
                ax.plot(kf.data["Time"], kf.data[column], lw=0.7, ls="--", color="#B0BEC5", alpha=0.6,
                        label=label + " (not used)", zorder=0)
        if n <= 3:
            _finish(ax, f"CD kinetics - {os.path.splitext(kf.name)[0]}")
    if n > 3:
        _finish(axes[0], "CD kinetics - all files")
    fig.tight_layout()


def average(fig, files, chosen, mean_df):
    """Selected traces and their average."""
    fig.clear()
    if mean_df is None:
        message(fig, "Select the traces to average on the 'Data' tab.")
        return
    ax1 = fig.add_subplot(211)
    for index, column in chosen:
        ax1.plot(files[index].data["Time"], files[index].data[column], lw=0.7,
                 label=f"{column} (CSV file {index + 1})")
    _finish(ax1, "Selected CD kinetics", xlabel="")
    ax2 = fig.add_subplot(212, sharex=ax1)
    ax2.plot(mean_df["Time"], mean_df[AVERAGE_COLUMN], lw=0.9, color="#1F4E9C", label="Average CD kinetics")
    _finish(ax2, "Average CD kinetics")
    fig.tight_layout()


def trimming(fig, mean_df, n_begin, n_end, n_show=50):
    """First points of the average with the removed ones marked; whole trace after trimming."""
    fig.clear()
    if mean_df is None:
        message(fig, "Select the traces to average on the 'Data' tab.")
        return
    t = mean_df["Time"].to_numpy()
    y = mean_df[AVERAGE_COLUMN].to_numpy()
    n = len(t)
    keep = slice(n_begin, n - n_end if n_end else n)
    ax1 = fig.add_subplot(121)
    m = min(n, max(n_show, n_begin + 10))
    ax1.plot(t[:m], y[:m], "-", color="#9DB7DD", lw=0.8)
    ax1.scatter(t[n_begin:m], y[n_begin:m], s=12, color="#1F4E9C", label="kept", zorder=3)
    if n_begin:
        ax1.scatter(t[:min(n_begin, m)], y[:min(n_begin, m)], s=40, marker="x", color="#C62828",
                    label=f"removed ({n_begin})", zorder=4)
    _finish(ax1, f"Beginning - first {m} points")
    ax2 = fig.add_subplot(122)
    ax2.plot(t[keep], y[keep], lw=0.8, color="#1F4E9C", label="kept")
    if n_end:
        ax2.plot(t[n - n_end:], y[n - n_end:], lw=0.8, color="#C62828", label=f"removed at the end ({n_end})")
    if n_begin:
        ax2.plot(t[:n_begin], y[:n_begin], "x", color="#C62828")
    _finish(ax2, "Whole trace after trimming")
    fig.tight_layout()


def converted(fig, kinetics_df):
    fig.clear()
    if kinetics_df is None:
        message(fig, "Set the conversion parameters on the 'Processing' tab.")
        return
    ax = fig.add_subplot(111)
    ax.plot(kinetics_df["Time"], kinetics_df[AVERAGE_COLUMN], lw=0.9, color="#1F4E9C",
            label="Average CD kinetics after conversion")
    _finish(ax, "Average CD kinetics after conversion to Δε", ylabel=DELTA_EPS)
    fig.tight_layout()


def fit_and_residuals(fig, result, show_smoothed=True, log_x=False):
    """Data + fit (top, 2/3) and residuals (bottom, 1/3) of one model."""
    fig.clear()
    if result is None:
        message(fig, "No fit yet - choose a model and press Fit.")
        return
    gs = fig.add_gridspec(3, 1, hspace=0.08)
    ax1 = fig.add_subplot(gs[:2, 0])
    ax2 = fig.add_subplot(gs[2, 0], sharex=ax1)
    x, y = result["x"], result["y"]
    ax1.plot(x, y, "o", ms=2.5, color="#5B8DD6", alpha=0.6, label="Data")
    ax1.plot(x, result["fitted"], "-", color="red", lw=1.6, label="Fit")
    _finish(ax1, result.get("fit_title", result["model"]), xlabel="", ylabel=DELTA_EPS)
    ax1.tick_params(labelbottom=False)
    ax2.plot(x, result["residuals"], "o", ms=2, color="green", alpha=0.6, label="Residuals")
    if show_smoothed and result.get("smoothed_residuals") is not None:
        ax2.plot(x, result["smoothed_residuals"], "-", color="blue", lw=1.2, label="Smoothed")
    ax2.axhline(0, color="red", ls="--", lw=1)
    _finish(ax2, "", ylabel="Residuals")
    if log_x and (x > 0).all():
        ax1.set_xscale("log")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.93, bottom=0.1)


def fit_only(fig, result):
    """The notebook's fit figure (for the Excel export)."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.plot(result["x"], result["y"], "o", markersize=3, label="Data")
    ax.plot(result["x"], result["fitted"], "-", label="Fit", color="red")
    _finish(ax, result.get("fit_title", result["model"]), ylabel=DELTA_EPS)


def residuals_only(fig, result):
    """The notebook's residual figure (for the Excel export)."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.plot(result["x"], result["residuals"], "o", markersize=3, label="Original Residuals", color="green")
    if result.get("smoothed_residuals") is not None:
        ax.plot(result["x"], result["smoothed_residuals"], "-", label="Smoothed Residuals", color="blue")
    ax.axhline(0, color="red", linestyle="--")
    _finish(ax, result.get("res_title", "Residuals"), ylabel="Residuals")


def model_comparison(fig, results):
    """All fitted models over the data (top) and their residuals (bottom)."""
    fig.clear()
    if not results:
        message(fig, "Fit at least one model to compare.")
        return
    gs = fig.add_gridspec(3, 1, hspace=0.08)
    ax1 = fig.add_subplot(gs[:2, 0])
    ax2 = fig.add_subplot(gs[2, 0], sharex=ax1)
    first = next(iter(results.values()))
    ax1.plot(first["x"], first["y"], "o", ms=2, color="#AAAAAA", label="Data")
    for name, r in results.items():
        line, = ax1.plot(r["x"], r["fitted"], "-", lw=1.4, label=name)
        ax2.plot(r["x"], r["residuals"], ".", ms=1.5, color=line.get_color(), alpha=0.5)
    ax2.axhline(0, color="black", ls="--", lw=1)
    _finish(ax1, "Comparison of the fitted models", xlabel="", ylabel=DELTA_EPS)
    ax1.tick_params(labelbottom=False)
    _finish(ax2, "", ylabel="Residuals", legend=False)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.93, bottom=0.1)


def f_test(fig, t):
    fig.clear()
    if t is None:
        message(fig, "No F-test yet - choose a comparison and press Run F-test.")
        return
    short = t.get("short", ("Simple", "Complex"))
    gs = fig.add_gridspec(3, 1, hspace=0.08)
    ax1 = fig.add_subplot(gs[:2, 0])
    ax2 = fig.add_subplot(gs[2, 0], sharex=ax1)
    ax1.plot(t["x"], t["y"], "o", ms=2.5, color="blue", alpha=0.5, label="Data")
    ax1.plot(t["x"], t["fit_simple"]["fitted"], "-", color="red", label=f"{short[0]} Exponential Fit")
    ax1.plot(t["x"], t["fit_complex"]["fitted"], "--", color="green", label=f"{short[1]} Exponential Fit")
    _finish(ax1, f"F-test: {t['simple']} vs {t['complex']}", xlabel="", ylabel=DELTA_EPS)
    ax1.tick_params(labelbottom=False)
    ax2.plot(t["x"], t["fit_simple"]["residuals"], "o", ms=2, color="red", alpha=0.5, label=f"Residuals {short[0]}")
    ax2.plot(t["x"], t["fit_complex"]["residuals"], "x", ms=2, color="green", alpha=0.5, label=f"Residuals {short[1]}")
    ax2.axhline(0, color="black", ls="--", lw=1)
    _finish(ax2, "", ylabel="Residuals")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.93, bottom=0.1)


def render_png(draw, *args, figsize=(12, 6), dpi=100, **kwargs):
    """Draw with `draw(fig, ...)` on an off-screen figure and return PNG bytes."""
    fig = Figure(figsize=figsize, dpi=dpi)
    draw(fig, *args, **kwargs)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()
