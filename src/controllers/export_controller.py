# src/controllers/export_controller.py
"""Step 5 - Excel workbook, CSV table, plots, report."""

import os

from PyQt5.QtWidgets import QFileDialog

from src.modules.analysis.models import MODEL_NAMES
from src.modules.export.excel_export import ExportError, default_output_path, export_results, export_table_csv
from src.modules.utils.system import open_with_system
from src.views import icons


class ExportController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        w = app.window
        self.panel = p = w.export_panel
        self._user_path = False
        p.browse_button.clicked.connect(self.browse)
        p.path_edit.textEdited.connect(lambda _: setattr(self, "_user_path", True))
        p.export_button.clicked.connect(self.export_excel)
        p.csv_button.clicked.connect(self.export_csv)
        p.plots_button.clicked.connect(self.export_plots)
        p.report_button.clicked.connect(self.save_report)
        p.project_button.clicked.connect(lambda: app.save_project(ask=True))
        p.open_folder_button.clicked.connect(self.open_folder)
        w.actions["export_excel"].triggered.connect(self.export_excel)
        w.actions["export_csv"].triggered.connect(self.export_csv)
        w.actions["export_plots"].triggered.connect(self.export_plots)
        w.actions["save_report"].triggered.connect(self.save_report)
        w.results_panel.save_report_button.clicked.connect(self.save_report)
        app.signals.fitsChanged.connect(self.refresh)
        app.signals.processingChanged.connect(self.refresh)
        app.signals.filesChanged.connect(self._files_changed)
        self.refresh()

    # ------------------------------------------------------------------ window state (project)
    def view_state(self):
        p = self.panel
        return {"export_model": p.model_combo.currentData(),
                "export_path": p.path_edit.text() if self._user_path else "",
                "export_figures": p.figures_check.isChecked(), "export_open_after": p.open_after_check.isChecked()}

    def apply_view_state(self, st):
        p = self.panel
        p.figures_check.setChecked(bool(st.get("export_figures", True)))
        p.open_after_check.setChecked(bool(st.get("export_open_after", True)))
        if st.get("export_path"):
            p.path_edit.setText(st["export_path"])
            self._user_path = True
        i = p.model_combo.findData(st.get("export_model"))
        if i >= 0:
            p.model_combo.setCurrentIndex(i)

    def _files_changed(self):
        if not self._user_path:
            self.panel.path_edit.setText(default_output_path(self.session.files) if self.session.files else "")
        self.refresh()

    def refresh(self):
        combo = self.panel.model_combo
        previous = combo.currentData()
        fits = self.session.current_fits()
        combo.blockSignals(True)
        combo.clear()
        for name in MODEL_NAMES:
            if name in fits:
                combo.addItem(icons.get("fit"), f"{name.capitalize()}  (R² = {fits[name]['r_squared']:.4f})", name)
        shown = self.app.fit.shown_model if hasattr(self.app, "fit") else None
        for want in (shown, previous):
            i = combo.findData(want)
            if i >= 0:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        ok = combo.count() > 0
        self.panel.export_button.setEnabled(ok)
        self.app.window.actions["export_excel"].setEnabled(ok)
        if not ok:
            self.panel.status_label.setText("Fit a model (step 3) to enable the export.")
        elif not self.panel.status_label.text().startswith("✔"):
            self.panel.status_label.setText("")

    def browse(self):
        start = self.panel.path_edit.text() or os.path.join(self.app.last_dir(), "results CD.xlsx")
        path, _ = QFileDialog.getSaveFileName(self.app.window, "Excel workbook", start, "Excel workbook (*.xlsx)")
        if path:
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self.panel.path_edit.setText(path)
            self._user_path = True

    def export_excel(self):
        name = self.panel.model_combo.currentData()
        fit = self.session.fits.get(name) if name else None
        if fit is None or self.session.result is None:
            self.app.error("Export", "Fit a model to the current data first (step 3).")
            return
        path = self.panel.path_edit.text().strip()
        if not path:
            self.browse()
            path = self.panel.path_edit.text().strip()
            if not path:
                return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            export_results(path, self.session.files, self.session.result, fit,
                           list(self.session.f_tests.values()), include_figures=self.panel.figures_check.isChecked(),
                           spectra=self.app.data.spectra_plot_options())
        except (ExportError, OSError) as exc:
            self.app.error("Export to Excel", str(exc))
            return
        self.app.set_last_dir(path)
        self.panel.status_label.setText(f"✔ Saved: {path}")
        self.app.status(f"Results ({name}) saved to {path}")
        self.app.window.results_panel.append_report(f"Excel export: {name} -> {path}")
        if self.panel.open_after_check.isChecked():
            try:
                open_with_system(path)
            except OSError as exc:
                self.app.status(f"Saved, but cannot open it: {exc}")

    def export_csv(self):
        if self.session.result is None:
            self.app.error("Export", "There are no converted kinetics to export.")
            return
        start = os.path.join(self._out_dir(), "kinetics_with_fits.csv")
        path, _ = QFileDialog.getSaveFileName(self.app.window, "Data table", start, "CSV file (*.csv)")
        if not path:
            return
        try:
            export_table_csv(path, self.session.result, self.session.fits)
        except OSError as exc:
            self.app.error("Export", f"Cannot write the file:\n{exc}")
            return
        self.app.set_last_dir(path)
        self.app.status(f"Data table saved: {path}")

    def export_plots(self):
        d = QFileDialog.getExistingDirectory(self.app.window, "Folder for the plots", self._out_dir())
        if not d:
            return
        saved = 0
        for key, panel in self.app.window.plots.items():
            try:
                panel.figure.savefig(os.path.join(d, f"{key}.png"), dpi=300)
                saved += 1
            except Exception as exc:          # noqa: BLE001
                self.app.status(f"Plot {key} not saved: {exc}")
        self.app.set_last_dir(d)
        self.app.status(f"{saved} plots saved to {d}")

    def save_report(self):
        start = os.path.join(self._out_dir(), "fit_report.txt")
        path, _ = QFileDialog.getSaveFileName(self.app.window, "Report", start, "Text file (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.app.window.results_panel.report.toPlainText())
        except OSError as exc:
            self.app.error("Save report", str(exc))
            return
        self.app.status(f"Report saved: {path}")

    def open_folder(self):
        path = self.panel.path_edit.text().strip()
        d = os.path.dirname(path) if path else self._out_dir()
        if d and os.path.isdir(d):
            open_with_system(d)

    def _out_dir(self):
        path = self.panel.path_edit.text().strip()
        if path and os.path.isdir(os.path.dirname(path)):
            return os.path.dirname(path)
        return self.app.last_dir()
