# src/controllers/compare_controller.py
"""Step 4 - the model comparison table and the F-tests of nested models."""

import copy

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QGuiApplication
from PyQt5.QtWidgets import QTableWidgetItem

from src.controllers.worker import TaskRunner
from src.modules.analysis import fitting
from src.modules.analysis.models import MODEL_NAMES, default_f_tests
from src.modules.analysis.processing import AVERAGE_COLUMN
from src.modules.visualization import figures
from src.views.widgets import format_number, parse_list


class CompareController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        w = app.window
        self.panel = p = w.compare_panel
        self.results = w.results_panel
        self.runner = TaskRunner()
        self.shown_test = None

        p.show_comparison_button.clicked.connect(self.show_comparison)
        p.ftest_combo.currentIndexChanged.connect(self._test_changed)
        p.p0_simple_edit.editingFinished.connect(lambda: self._p0_edited("p0_simple", p.p0_simple_edit))
        p.p0_complex_edit.editingFinished.connect(lambda: self._p0_edited("p0_complex", p.p0_complex_edit))
        p.reset_ftest_button.clicked.connect(self.reset_p0)
        p.run_ftest_button.clicked.connect(self.run_current)
        p.run_all_ftests_button.clicked.connect(self.run_all)
        w.actions["ftests"].triggered.connect(self.run_all)
        self.results.copy_comparison_button.clicked.connect(self.copy_table)
        self.runner.stepStarted.connect(lambda i, n, label: app.window.set_status(f"F-test {label} … ({i + 1}/{n})"))
        self.runner.stepDone.connect(self._done)
        self.runner.stepFailed.connect(self._failed)
        self.runner.busyChanged.connect(self._busy)

        app.signals.fitsChanged.connect(self.refresh_table)
        app.signals.processingChanged.connect(self._data_changed)
        app.signals.settingsReplaced.connect(self._test_changed)
        app.signals.ftestsChanged.connect(self._data_changed)
        self._test_changed()
        self.refresh_table()

    # ------------------------------------------------------------------ window state (project)
    def view_state(self):
        return {"f_test": self.test_name}

    def apply_view_state(self, st):
        i = self.panel.ftest_combo.findData(st.get("f_test"))
        if i >= 0:
            self.panel.ftest_combo.setCurrentIndex(i)
            t = self.session.f_tests.get(self.test_name)
            if t is not None:
                self.shown_test = self.test_name
                self._show_test(t)

    # ------------------------------------------------------------------ comparison
    def refresh_table(self):
        fits = self.session.current_fits()
        t = self.results.comparison_table
        t.setRowCount(0)
        order = [n for n in MODEL_NAMES if n in fits]
        if not order:
            self._redraw_comparison()
            return
        best_aic = min(fits[n]["aic"] for n in order)
        best_bic = min(fits[n]["bic"] for n in order)
        bold = QFont()
        bold.setBold(True)
        for name in order:
            f = fits[name]
            r = t.rowCount()
            t.insertRow(r)
            values = [name, f"{f['r_squared']:.5f}", f"{f['rmsd']:.4f}", f"{f['aic']:.2f}",
                      f"{f['aic'] - best_aic:.2f}", f"{f['bic']:.2f}", f"{f['bic'] - best_bic:.2f}",
                      f"{f['durbin_watson']:.3f}", f"{f['lag1_autocorr']:.3f}", str(f["n_params"]),
                      str(len(f["warnings"])) + ("  ⚠ lower minimum" if "LOWER minimum" in f["multistart"] else "")]
            for c, v in enumerate(values):
                item = QTableWidgetItem(v)
                if c > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if (c in (3, 4) and f["aic"] == best_aic) or (c in (5, 6) and f["bic"] == best_bic):
                    item.setFont(bold)
                    item.setForeground(QBrush(QColor("#1B5E20")))
                if c == 10 and (f["warnings"] or "LOWER" in f["multistart"]):
                    item.setForeground(QBrush(QColor("#B71C1C")))
                    item.setToolTip("\n".join(f["warnings"] + [f["multistart"]]))
                t.setItem(r, c, item)
        self._redraw_comparison()

    def _redraw_comparison(self):
        panel = self.app.window.plots["comparison"]
        figures.model_comparison(panel.figure, {n: f for n, f in self.session.current_fits().items()})
        panel.redraw()

    def show_comparison(self):
        self.refresh_table()
        self.app.window.show_plot("comparison")
        self.results.setCurrentIndex(1)

    def copy_table(self):
        t = self.results.comparison_table
        lines = ["\t".join(t.horizontalHeaderItem(c).text() for c in range(t.columnCount()))]
        for r in range(t.rowCount()):
            lines.append("\t".join(t.item(r, c).text() for c in range(t.columnCount())))
        QGuiApplication.clipboard().setText("\n".join(lines))
        self.app.status("Comparison table copied to the clipboard.")

    def _data_changed(self):
        self.refresh_table()
        current = self.session.current_f_tests()
        t = current.get(self.shown_test) if self.shown_test else None
        if t is None and current:
            t = next(iter(current.values()))
        self._show_test(t)
        self._result_text()

    # ------------------------------------------------------------------ F-tests
    @property
    def test_name(self):
        return self.panel.ftest_combo.currentData()

    def _test_changed(self, *_):
        d = self.session.f_test_defs[self.test_name]
        p = self.panel
        p.simple_label.setText(d["simple"])
        p.complex_label.setText(d["complex"])
        p.p0_simple_edit.setText(", ".join(format_number(v) for v in d["p0_simple"]))
        p.p0_complex_edit.setText(", ".join(format_number(v) for v in d["p0_complex"]))
        self._result_text()

    def _p0_edited(self, key, edit):
        d = self.session.f_test_defs[self.test_name]
        model = d["simple"] if key == "p0_simple" else d["complex"]
        n = len(self.session.specs[model]["names"])
        try:
            values = parse_list(edit.text())
            if len(values) != n:
                raise ValueError(f"{model} needs {n} values ({', '.join(self.session.specs[model]['names'])})")
            if not all(np.isfinite(values)):
                raise ValueError("the values must be finite numbers")
        except ValueError as exc:
            self.app.status(f"p0 not accepted: {exc}")
            edit.setText(", ".join(format_number(v) for v in d[key]))
            return
        d[key] = values

    def reset_p0(self):
        self.session.f_test_defs[self.test_name] = default_f_tests()[self.test_name]
        self._test_changed()

    def _make_step(self, name):
        r = self.session.result
        d = copy.deepcopy(self.session.f_test_defs[name])
        specs = copy.deepcopy(self.session.specs)
        x = r.kinetics_df["Time"].to_numpy(copy=True)
        y = r.kinetics_df[AVERAGE_COLUMN].to_numpy(copy=True)
        fp, label = r.fingerprint, r.y_label

        def run():
            t = fitting.run_nested_f_test(d["simple"], d["complex"], specs, x, y, d["p0_simple"], d["p0_complex"],
                                          fingerprint=fp, y_label=label)
            t["short"] = d["short"]
            t["name"] = name
            return t
        return name, run

    def _can_run(self):
        if self.session.result is None:
            self.app.error("F-test", "There are no converted kinetics.\n\n"
                           + (self.session.processing_error or "Load data first."))
            return False
        return not self.runner.busy

    def run_current(self):
        # take the p0 being typed, too
        self._p0_edited("p0_simple", self.panel.p0_simple_edit)
        self._p0_edited("p0_complex", self.panel.p0_complex_edit)
        if self._can_run():
            self.runner.start([self._make_step(self.test_name)])

    def run_all(self):
        if self._can_run():
            self.app.window.step_tabs.setCurrentWidget(self.panel)
            self.runner.start([self._make_step(n) for n in self.session.f_test_defs])

    def _busy(self, busy):
        for wdg in (self.panel.run_ftest_button, self.panel.run_all_ftests_button):
            wdg.setEnabled(not busy)
        self.app.window.actions["ftests"].setEnabled(not busy)

    def _done(self, name, t):
        self.session.f_tests[name] = t
        self.results.append_report(fitting.format_f_test_text(t))
        self.shown_test = name
        idx = self.panel.ftest_combo.findData(name)
        self.panel.ftest_combo.blockSignals(True)
        self.panel.ftest_combo.setCurrentIndex(idx)
        self.panel.ftest_combo.blockSignals(False)
        self._test_changed()
        self._show_test(t)
        self.app.window.show_plot("ftest")
        self.app.signals.fitsChanged.emit()          # the export lists the F-tests
        p = t["p_value"]
        self.app.status(f"F-test {name}: F = {t['F_stat']:.4g}, p = {'< 1e-300' if p == 0 else f'{p:.3g}'}")

    def _failed(self, name, message):
        self.results.append_report(f"=== F-test {name} ===\nFAILED: {message}")
        self.app.error("F-test failed", message)

    def _show_test(self, t):
        panel = self.app.window.plots["ftest"]
        figures.f_test(panel.figure, t)
        panel.redraw()

    def _result_text(self):
        t = self.session.f_tests.get(self.test_name)
        lab = self.panel.result_label
        if t is None:
            lab.setText("")
            return
        if not self.session.is_current(t):
            lab.setText("<span style='color:#B71C1C'>⚠ This F-test was made on other data – run it again.</span>")
            return
        p = t["p_value"]
        ptxt = "&lt; 1e-300" if p == 0 else f"{p:.3g}"
        verdict = ("<b style='color:#1B5E20'>the more complex model is significantly better</b>" if p < 0.05 else
                   "<b style='color:#E65100'>no significant improvement – keep the simpler model</b>")
        lab.setText(f"F = {t['F_stat']:.4g} (df {t['df_numerator']}, {t['df_residual']}), p = {ptxt}: {verdict}")
