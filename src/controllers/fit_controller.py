# src/controllers/fit_controller.py
"""Step 3 - model, p0/bounds, fitting (in the background) and the display of
the results."""

import copy

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QGuiApplication
from PyQt5.QtWidgets import QTableWidgetItem

from src.controllers.worker import TaskRunner
from src.modules.analysis import fitting
from src.modules.analysis.initial_guess import estimate_p0
from src.modules.analysis.models import EQUATIONS, MODEL_NAMES, default_specs
from src.modules.analysis.processing import AVERAGE_COLUMN
from src.modules.visualization import figures
import re

from src.views.widgets import format_number, parse_number


def equation_html(text):
    """'e^(−k·t)' -> e<sup>−k·t</sup> for the label of step 3."""
    return re.sub(r"e\^\(([^)]*)\)", r"e<sup>\1</sup>", text)

RED = QBrush(QColor("#B71C1C"))
GREY = QBrush(QColor("#90A4AE"))


class FitController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        w = app.window
        self.panel = p = w.fit_panel
        self.results = w.results_panel
        self.runner = TaskRunner()
        self.shown_model = None
        self._filling = False

        p.model_combo.currentIndexChanged.connect(self._model_changed)
        p.p0_table.itemChanged.connect(self._p0_edited)
        p.reset_p0_button.clicked.connect(self.reset_p0)
        p.use_fit_button.clicked.connect(self.use_fit_as_p0)
        p.guess_button.clicked.connect(self.estimate)
        p.multistart_spin.valueChanged.connect(lambda v: setattr(self.session, "check_starts", v))
        p.savgol_spin.valueChanged.connect(self._savgol_changed)
        p.smoothed_check.toggled.connect(lambda _: self.redraw())
        p.logx_check.toggled.connect(lambda _: self.redraw())
        p.fit_button.clicked.connect(self.fit_current)
        p.fit_all_button.clicked.connect(self.fit_all)
        w.actions["fit"].triggered.connect(self.fit_current)
        w.actions["fit_all"].triggered.connect(self.fit_all)
        w.actions["reset_models"].triggered.connect(self.reset_all_models)
        self.results.copy_params_button.clicked.connect(self.copy_tables)
        self.results.copy_report_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(self.results.report.toPlainText()))
        self.results.clear_report_button.clicked.connect(self.results.report.clear)

        self.runner.stepStarted.connect(self._step_started)
        self.runner.stepDone.connect(self._step_done)
        self.runner.stepFailed.connect(self._step_failed)
        self.runner.busyChanged.connect(self._busy)

        app.signals.processingChanged.connect(self._data_changed)
        app.signals.settingsReplaced.connect(self._settings_replaced)
        self._model_changed()

    # ------------------------------------------------------------------ window state (project)
    def view_state(self):
        p = self.panel
        return {"fit_model": self.model, "show_smoothed": p.smoothed_check.isChecked(),
                "log_time": p.logx_check.isChecked()}

    def apply_view_state(self, st):
        p = self.panel
        p.smoothed_check.setChecked(bool(st.get("show_smoothed", True)))
        p.logx_check.setChecked(bool(st.get("log_time", False)))
        if st.get("fit_model") in MODEL_NAMES:
            self.select_model(st["fit_model"])

    # ------------------------------------------------------------------ model and p0
    @property
    def model(self):
        return self.panel.model_combo.currentData()

    def _settings_replaced(self):
        p = self.panel
        p.multistart_spin.setValue(self.session.check_starts)
        p.savgol_spin.setValue(self.session.savgol_window)
        self._model_changed()

    def _model_changed(self, *_):
        name = self.model
        self.panel.equation_label.setText(equation_html(EQUATIONS[name]))
        self.fill_p0_table()
        self.shown_model = name
        self.show_result(self.session.fits.get(name))

    def fill_p0_table(self):
        spec = self.session.specs[self.model]
        t = self.panel.p0_table
        self._filling = True
        t.setRowCount(len(spec["names"]))
        for r, name in enumerate(spec["names"]):
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsEnabled)
            f = QFont()
            f.setBold(True)
            item.setFont(f)
            unit = "s⁻¹" if name in spec["rates"] else "M⁻¹cm⁻¹"
            item.setToolTip(f"{name} ({unit})")
            t.setItem(r, 0, item)
            for c, key in enumerate(("p0", "lower", "upper"), start=1):
                t.setItem(r, c, QTableWidgetItem(format_number(spec[key][r])))
        self._filling = False

    def _p0_edited(self, item):
        if self._filling or item.column() == 0:
            return
        spec = self.session.specs[self.model]
        r, c = item.row(), item.column()
        key = ("p0", "lower", "upper")[c - 1]
        old = spec[key][r]
        try:
            v = parse_number(item.text())
            if key == "p0" and not np.isfinite(v):
                raise ValueError("p0 must be a finite number")
            new = list(spec[key])
            new[r] = v
            lo = new[r] if key == "lower" else spec["lower"][r]
            hi = new[r] if key == "upper" else spec["upper"][r]
            p0 = new[r] if key == "p0" else spec["p0"][r]
            if not lo < hi:
                raise ValueError("the lower bound must be smaller than the upper bound")
            if not lo <= p0 <= hi:
                raise ValueError(f"p0 of {spec['names'][r]} must lie between its bounds")
        except ValueError as exc:
            self.app.status(f"Value not accepted: {exc}")
            self._filling = True
            item.setText(format_number(old))
            self._filling = False
            return
        spec[key] = new
        self._filling = True
        item.setText(format_number(v))
        self._filling = False

    def reset_p0(self):
        self.session.specs[self.model] = default_specs()[self.model]
        self.fill_p0_table()
        self.app.status(f"p0 and bounds of {self.model} reset.")

    def reset_all_models(self):
        self.session.specs = default_specs()
        self.fill_p0_table()
        self.app.status("p0 and bounds of all models reset to the original analysis.")

    def use_fit_as_p0(self):
        fit = self.session.fits.get(self.model)
        if fit is None:
            self.app.status(f"{self.model} has not been fitted yet.")
            return
        spec = self.session.specs[self.model]
        spec["p0"] = [float(f"{v:.6g}") for v in fit["params"]]
        self.fill_p0_table()
        self.app.status("The fitted values are the new p0.")

    def estimate(self):
        r = self.session.result
        if r is None:
            self.app.status("No data to estimate from.")
            return
        spec = self.session.specs[self.model]
        spec["p0"] = estimate_p0(spec, r.kinetics_df["Time"].values, r.kinetics_df[AVERAGE_COLUMN].values)
        self.fill_p0_table()
        self.app.status(f"p0 of {self.model} estimated from the data – press Fit.")

    def _savgol_changed(self, v):
        if v % 2 == 0:
            self.panel.savgol_spin.setValue(v + 1)
            return
        self.session.savgol_window = v
        for fit in self.session.fits.values():
            fit["smoothed_residuals"] = fitting.smooth_residuals(fit["residuals"], v)
        self.redraw()

    # ------------------------------------------------------------------ fitting
    def _make_step(self, name):
        r = self.session.result
        spec = copy.deepcopy(self.session.specs[name])
        x = r.kinetics_df["Time"].to_numpy(copy=True)
        y = r.kinetics_df[AVERAGE_COLUMN].to_numpy(copy=True)
        starts, window, fp, label = self.session.check_starts, self.session.savgol_window, r.fingerprint, r.y_label
        return name, lambda: fitting.fit_model(name, spec, x, y, check_starts=starts, savgol_window=window,
                                               fingerprint=fp, y_label=label)

    def _can_fit(self):
        if self.session.result is None:
            self.app.error("Fit", "There are no converted kinetics to fit.\n\n"
                           + (self.session.processing_error or "Load data first."))
            return False
        if self.runner.busy:
            self.app.status("A fit is already running.")
            return False
        return True

    def fit_current(self):
        if self._can_fit():
            self.app.window.step_tabs.setCurrentWidget(self.panel)
            self.runner.start([self._make_step(self.model)])

    def fit_all(self):
        if self._can_fit():
            self._batch = True
            self.app.window.step_tabs.setCurrentWidget(self.panel)
            self.runner.start([self._make_step(n) for n in MODEL_NAMES])

    def _busy(self, busy):
        p = self.panel
        for wdg in (p.fit_button, p.fit_all_button):
            wdg.setEnabled(not busy)
        for k in ("fit", "fit_all"):
            self.app.window.actions[k].setEnabled(not busy)
        if busy:
            self.app.window.setCursor(Qt.BusyCursor)
            return
        self.app.window.unsetCursor()
        if getattr(self, "_batch", False):
            self._batch = False
            fits = self.session.current_fits()
            if fits:
                best = min(fits.values(), key=lambda f: f["aic"])
                self.select_model(best["model"])
                self.app.status(f"All models fitted; the lowest AIC: {best['model']} "
                                f"(see the Model comparison table).")
                self.app.window.results_panel.setCurrentIndex(1)

    def _step_started(self, i, total, label):
        self.panel.status_label.setText(f"Fitting {label} … ({i + 1}/{total})")
        self.app.window.set_status(f"Fitting {label} … ({i + 1}/{total})")

    def _step_done(self, label, result):
        self.session.fits[label] = result
        self.results.append_report(fitting.format_result_text(result))
        self.select_model(label)
        self.app.window.show_plot("fit")
        self.app.signals.fitsChanged.emit()
        warn = f" – {len(result['warnings'])} warning(s)" if result["warnings"] else ""
        self.app.status(f"{label}: R² = {result['r_squared']:.4f}, AIC = {result['aic']:.1f}{warn}")

    def select_model(self, name):
        """Show the model `name` in step 3 (its p0 and its fit)."""
        if name != self.model:
            idx = self.panel.model_combo.findData(name)
            self.panel.model_combo.blockSignals(True)
            self.panel.model_combo.setCurrentIndex(idx)
            self.panel.model_combo.blockSignals(False)
            self.panel.equation_label.setText(equation_html(EQUATIONS[name]))
            self.fill_p0_table()
        self.show_result(self.session.fits.get(name))

    def _step_failed(self, label, message):
        self.results.append_report(f"=== {label} ===\nFIT FAILED: {message}")
        self.panel.status_label.setText(f"✘ {label}: the fit failed – see the Report.")
        if not getattr(self, "_batch", False):
            self.app.error("Fit failed", message)

    # ------------------------------------------------------------------ results display
    def _data_changed(self):
        self.show_result(self.session.fits.get(self.shown_model))

    def show_result(self, fit):
        self.shown_model = fit["model"] if fit else self.model
        self._fill_tables(fit)
        self.redraw()
        current = self.session.is_current(fit)
        if fit is None:
            self.panel.status_label.setText("Not fitted yet." if self.session.result is not None else "")
        elif current:
            warn = f" – {len(fit['warnings'])} warning(s)" if fit["warnings"] else ""
            self.panel.status_label.setText(f"✔ {fit['model']} fitted (R² = {fit['r_squared']:.4f}){warn}")
        elif not current:
            self.panel.status_label.setText("⚠ The shown fit is outdated (the data were changed) – fit again.")

    def redraw(self):
        fit = self.session.fits.get(self.shown_model)
        panel = self.app.window.plots["fit"]
        if fit is not None and not self.session.is_current(fit):
            fit = dict(fit, fit_title=fit.get("fit_title", "") + "   [OUTDATED – fit again]")
        figures.fit_and_residuals(panel.figure, fit, show_smoothed=self.panel.smoothed_check.isChecked(),
                                  log_x=self.panel.logx_check.isChecked())
        panel.redraw()

    def _fill_tables(self, fit):
        pt, st = self.results.params_table, self.results.stats_table
        pt.setRowCount(0)
        st.setRowCount(0)
        if fit is None:
            return
        outdated = not self.session.is_current(fit)
        for label, value, lo, hi, unit in fit["rows"]:
            r = pt.rowCount()
            pt.insertRow(r)
            digits = 6 if unit == "s^-1" else 5
            for c, v in enumerate((label, format_number(value, digits), format_number(lo, digits),
                                   format_number(hi, digits), unit.replace("^-1", "⁻¹"))):
                item = QTableWidgetItem(v)
                if c in (1, 2, 3):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if outdated:
                    item.setForeground(GREY)
                pt.setItem(r, c, item)
        rows = [("Model", fit["model"]), ("R²", f"{fit['r_squared']:.5f}"), ("RMSD", f"{fit['rmsd']:.4f}"),
                ("AIC", f"{fit['aic']:.3f}"), ("BIC", f"{fit['bic']:.3f}"),
                ("AIC (log-likelihood)", f"{fit['aic2']:.3f}"), ("BIC (log-likelihood)", f"{fit['bic2']:.3f}"),
                ("Durbin-Watson", f"{fit['durbin_watson']:.4f}"), ("Lag-1 autocorrelation", f"{fit['lag1_autocorr']:.4f}"),
                ("Points / parameters", f"{fit['n_points']} / {fit['n_params']}"),
                ("Equation", fit["equation"]), ("Multi-start check", fit["multistart"])]
        rows += [("Warning", m) for m in fit["warnings"]]
        if outdated:
            rows.insert(0, ("Status", "OUTDATED – made on other data; fit again"))
        for label, v in rows:
            r = st.rowCount()
            st.insertRow(r)
            a, b = QTableWidgetItem(label), QTableWidgetItem(v)
            b.setToolTip(v)
            if label in ("Warning", "Status") or "LOWER minimum" in v:
                a.setForeground(RED)
                b.setForeground(RED)
            st.setItem(r, 0, a)
            st.setItem(r, 1, b)
        self.results.setCurrentIndex(0)

    def copy_tables(self):
        out = []
        for t in (self.results.params_table, self.results.stats_table):
            headers = [t.horizontalHeaderItem(c).text() for c in range(t.columnCount())]
            out.append("\t".join(headers))
            for r in range(t.rowCount()):
                out.append("\t".join(t.item(r, c).text() if t.item(r, c) else "" for c in range(t.columnCount())))
            out.append("")
        QGuiApplication.clipboard().setText("\n".join(out))
        self.app.status("Tables copied to the clipboard.")
