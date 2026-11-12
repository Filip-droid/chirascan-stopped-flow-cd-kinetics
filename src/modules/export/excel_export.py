# src/modules/export/excel_export.py
"""Section 7 of the notebook: everything on one sheet "Results" of an Excel
workbook - the summary (metadata of the CSV files used, analysis inputs, fit
results with 95 % CI, goodness of fit, equation, F-tests, software versions)
and the two figures on the left, the data tables (original data of the traces
that were averaged, then the converted kinetics with the fit and the
residuals) side by side on the right. Unticked traces, and files none of whose
traces is ticked, are not exported (the notebook exported all of them).
The ticked spectra, as drawn in the plot "Spectra", go to a second sheet."""

import io
import os
import platform
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd
import scipy

from src.modules.analysis.processing import AVERAGE_COLUMN
from src.modules.data_io.chirascan_reader import METADATA_COLUMNS
from src.modules.visualization import figures
from src.version import ANALYSIS_VERSION, APP_NAME, APP_VERSION

DATA_START_COL = 9  # column J; the summary and figures occupy columns A-H


class ExportError(RuntimeError):
    pass


def default_output_path(files):
    """Next to the first data file - or in Documents when that folder cannot be written (the example
    data inside the installed program)."""
    directory = os.path.dirname(files[0].path) if files else ""
    if not directory or not os.access(directory, os.W_OK):
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        directory = docs if os.path.isdir(docs) else os.path.expanduser("~")
    return os.path.join(directory, "results CD.xlsx")


def export_results(output_filename, files, processing, fit, f_tests=(), include_figures=True, spectra=None):
    """Write the workbook. `processing` is a ProcessingResult, `fit` a fit result
    dictionary of the same data, `f_tests` the F-test results to include, `spectra` the
    options of the plot 'Spectra' (items, prop, baseline, hv_max, ...) or None."""
    if fit is None:
        raise ExportError("No fitted model to export.")
    if fit["data_fingerprint"] != processing.fingerprint:
        raise ExportError(
            f"The stored fit of {fit['model']!r} was made on different data than the current kinetics "
            f"(the selection, trimming or conversion was changed afterwards). Fit the model again.")
    kinetics_df = processing.kinetics_df
    model_name = fit["model"]
    used = selected_traces(files, processing)
    try:
        import xlsxwriter
    except ModuleNotFoundError as exc:
        raise ExportError("The 'xlsxwriter' package is required for the Excel export "
                          "(pip install xlsxwriter).") from exc
    try:
        with pd.ExcelWriter(output_filename, engine="xlsxwriter") as writer:
            workbook = writer.book
            ws = workbook.add_worksheet("Results")
            writer.sheets["Results"] = ws

            bold = workbook.add_format({"bold": True})
            title = workbook.add_format({"bold": True, "font_size": 14})
            header = workbook.add_format({"bold": True, "bottom": 1})
            num4 = workbook.add_format({"num_format": "0.0000"})
            num5 = workbook.add_format({"num_format": "0.00000"})
            sci = workbook.add_format({"num_format": "0.00E+00"})

            ws.set_column(0, 0, 36)
            ws.set_column(1, 3, 14)
            ws.set_column(4, 4, 16)
            ws.set_column(5, 5, 14)

            r = 0
            ws.write(r, 0, "Stopped-flow CD kinetic analysis", title); r += 1
            ws.write(r, 0, "Exported on:"); ws.write(r, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")); r += 2

            ws.write(r, 0, "Metadata of the CSV files", bold); r += 1
            for c, name in enumerate(METADATA_COLUMNS):
                ws.write(r, c, name, header)
            r += 1
            for kf, _ in used:
                for c, name in enumerate(METADATA_COLUMNS):
                    value = os.path.basename(kf.metadata[name]) if name == "File" else kf.metadata[name]
                    ws.write(r, c, value)
                r += 1
            r += 1

            ws.write(r, 0, "Analysis inputs", bold); r += 1
            for key, value in processing.analysis_inputs.items():
                ws.write(r, 0, key)
                if isinstance(value, list):
                    ws.write(r, 1, "; ".join(value))
                elif isinstance(value, (int, float, np.integer, np.floating)):
                    ws.write_number(r, 1, float(value))
                else:
                    ws.write(r, 1, str(value))
                r += 1
            ws.write(r, 0, "Initial guesses p0"); ws.write(r, 1, ", ".join(f"{v:g}" for v in fit["p0_used"])); r += 1
            if fit.get("fixed"):
                ws.write(r, 0, "Fixed parameters (not fitted)")
                ws.write(r, 1, ", ".join(f"{n} = {fit['par'][n]:g}" for n in fit["fixed"])); r += 1
            r += 1

            ws.write(r, 0, f"Fit results - {model_name}", bold); r += 1
            for c, name in enumerate(["Parameter", "Value", "95 % CI lower", "95 % CI upper", "Unit"]):
                ws.write(r, c, name, header)
            r += 1
            for label, value, lo, hi, unit in fit["rows"]:
                fmt = num5 if unit == "s^-1" else num4
                ws.write(r, 0, label)
                _num(ws, r, 1, value, fmt)
                if lo is not None:
                    _num(ws, r, 2, lo, fmt)
                    _num(ws, r, 3, hi, fmt)
                ws.write(r, 4, unit)
                r += 1
            r += 1

            ws.write(r, 0, "Goodness of fit", bold); r += 1
            for label, value in (("R^2", fit["r_squared"]), ("RMSD", fit["rmsd"]), ("AIC", fit["aic"]),
                                 ("BIC", fit["bic"]), ("Durbin-Watson", fit["durbin_watson"]),
                                 ("Lag-1 residual autocorrelation", fit["lag1_autocorr"]),
                                 ("Number of points", fit["n_points"]), ("Number of fitted parameters", fit["n_params"])):
                ws.write(r, 0, label); _num(ws, r, 1, value, num4); r += 1
            ws.write(r, 0, "Equation"); ws.write(r, 1, fit["equation"]); r += 1
            ws.write(r, 0, "Multi-start check"); ws.write(r, 1, fit["multistart"]); r += 1
            for msg in fit["warnings"]:
                ws.write(r, 0, "Fit warning"); ws.write(r, 1, msg); r += 1
            r += 1

            current = [t for t in f_tests if t["data_fingerprint"] == processing.fingerprint]
            if current:
                ws.write(r, 0, "F-tests of nested models", bold); r += 1
                for c, name in enumerate(["Comparison", "F", "p-value", "df numerator", "df residual"]):
                    ws.write(r, c, name, header)
                r += 1
                for t in current:
                    ws.write(r, 0, f"{t['simple']} vs {t['complex']}")
                    _num(ws, r, 1, t["F_stat"], num4)
                    if t["p_value"] == 0:
                        ws.write(r, 2, "< 1e-300")
                    else:
                        _num(ws, r, 2, t["p_value"], sci)
                    ws.write_number(r, 3, t["df_numerator"])
                    ws.write_number(r, 4, t["df_residual"])
                    r += 1
                r += 1

            ws.write(r, 0, "Software", bold); r += 1
            for name, version in (("Program", f"{APP_NAME} {APP_VERSION}"),
                                  ("Analysis script version", ANALYSIS_VERSION),
                                  ("Python", platform.python_version()),
                                  ("numpy", np.__version__), ("scipy", scipy.__version__),
                                  ("pandas", pd.__version__), ("matplotlib", matplotlib.__version__),
                                  ("xlsxwriter", xlsxwriter.__version__)):
                ws.write(r, 0, name); ws.write(r, 1, version); r += 1
            r += 1

            if include_figures:
                for key, draw in (("fit", figures.fit_only), ("residuals", figures.residuals_only)):
                    png = figures.render_png(draw, fit)
                    ws.insert_image(r, 0, f"{key}.png", {"image_data": io.BytesIO(png),
                                                         "x_scale": 0.7, "y_scale": 0.7})
                    r += 23

            col = DATA_START_COL
            for kf, columns in used:
                df = kf.data[["Time"] + columns]
                out = df.rename(columns={c: (f"{c} (mdeg)" if c != "Time" else "Time (s)") for c in df.columns})
                ws.write(0, col, f"Original data - {kf.name} (traces used)", bold)
                out.to_excel(writer, sheet_name="Results", startrow=1, startcol=col, index=False)
                col += out.shape[1] + 1

            conv = pd.DataFrame({
                "Time (s)": kinetics_df["Time"].values,
                ("Average CD kinetics (delta epsilon, M^-1 cm^-1 per nucleotide)" if processing.basis == "nucleotide"
                 else "Average CD kinetics (delta epsilon, M^-1 cm^-1 per strand)"): kinetics_df[AVERAGE_COLUMN].values,
                f"Fit ({model_name})": fit["fitted"],
                "Residuals": fit["residuals"],
            })
            ws.write(0, col, "Converted kinetics with fit", bold)
            conv.to_excel(writer, sheet_name="Results", startrow=1, startcol=col, index=False)

            if spectra and spectra.get("items"):
                write_spectra_sheet(writer, workbook, spectra, include_figures)
    except PermissionError as exc:
        raise ExportError(f"Cannot write {output_filename!r}. Close the file if it is open in Excel "
                          f"and try again.") from exc
    return output_filename


def spectra_table(items, prop="CircularDichroism", baseline=None, hv_max=None, **_):
    """[(spectrum, x, y)] of the spectra as drawn in the plot 'Spectra'."""
    from src.modules.data_io.spectra import subtract
    base = baseline.curve(prop, hv_max) if baseline is not None else None
    out = []
    for sp in items:
        if sp is baseline:
            continue
        c = sp.curve(prop, hv_max)
        if c is None:
            continue
        if base is not None:
            c = subtract(c, base)
        out.append((sp, c[0], c[1]))
    return out


def write_spectra_sheet(writer, workbook, options, include_figure=True):
    from src.modules.data_io.spectra import PROPERTY_LABELS
    rows = spectra_table(**options)
    if not rows:
        return
    ws = workbook.add_worksheet("Spectra")
    writer.sheets["Spectra"] = ws
    bold = workbook.add_format({"bold": True})
    prop = options.get("prop", "CircularDichroism")
    label = PROPERTY_LABELS.get(prop, prop)
    baseline, hv_max = options.get("baseline"), options.get("hv_max")
    ws.write(0, 0, "Spectra (as shown in the plot 'Spectra')", bold)
    ws.write(1, 0, f"Quantity: {label}")
    ws.write(2, 0, f"Baseline subtracted: {baseline.name if baseline is not None else 'none'}")
    ws.write(3, 0, f"Points with HV > {hv_max:g} V left empty" if hv_max is not None else "All points (no HV limit)")
    col = 0
    for sp, x, y in rows:
        df = pd.DataFrame({"Wavelength (nm)": x, f"{sp.stem} - {label}": y})
        ws.write(5, col, sp.name, bold)
        df.to_excel(writer, sheet_name="Spectra", startrow=6, startcol=col, index=False)
        ws.set_column(col, col + 1, 16)
        col += 3
    if include_figure:
        png = figures.render_png(figures.spectra, **options)
        ws.insert_image(1, col + 1, "spectra.png", {"image_data": io.BytesIO(png), "x_scale": 0.7, "y_scale": 0.7})


def selected_traces(files, processing):
    """[(file, [its traces that were averaged])] - only these go into the export; files without a
    selected trace are left out."""
    chosen = processing.chosen_columns
    if chosen is None:                      # (results made before this was recorded: everything)
        return [(kf, list(kf.traces)) for kf in files]
    out = []
    for i, kf in enumerate(files):
        columns = [c for j, c in chosen if j == i and c in kf.traces]
        if columns:
            out.append((kf, columns))
    return out


def _num(ws, r, c, value, fmt):
    v = float(value)
    if np.isfinite(v):
        ws.write_number(r, c, v, fmt)
    else:
        ws.write(r, c, str(v))


def export_table_csv(path, processing, fits):
    """Converted kinetics with the fit and residuals of every fitted model (CSV)."""
    df = pd.DataFrame({"Time (s)": processing.kinetics_df["Time"].values,
                       ("Delta epsilon (M^-1 cm^-1 per nucleotide)" if processing.basis == "nucleotide"
                        else "Delta epsilon (M^-1 cm^-1 per strand)"): processing.kinetics_df[AVERAGE_COLUMN].values})
    for name, fit in fits.items():
        if fit["data_fingerprint"] == processing.fingerprint:
            df[f"Fit ({name})"] = fit["fitted"]
            df[f"Residuals ({name})"] = fit["residuals"]
    df.to_csv(path, index=False)
    return path
