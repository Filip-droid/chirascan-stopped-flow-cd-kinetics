# src/controllers/data_controller.py
"""Step 1 - loading the files and choosing the traces."""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QTreeWidgetItem

from src.modules.data_io.chirascan_reader import data_files_in
from src.modules.data_io.spectra import PROPERTY_NAMES
from src.modules.utils.resource_path import example_path
from src.modules.visualization import figures
from src.views import icons


class DataController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        w = app.window
        self.panel = p = w.data_panel
        p.open_folder_button.clicked.connect(self.open_folder)
        p.add_files_button.clicked.connect(self.add_files)
        p.example_button.clicked.connect(self.load_example)
        p.remove_button.clicked.connect(self.remove_selected)
        p.clear_button.clicked.connect(self.clear_all)
        p.select_all_button.clicked.connect(lambda: self._check_all(True))
        p.select_none_button.clicked.connect(lambda: self._check_all(False))
        p.traces_tree.itemChanged.connect(self._tree_changed)
        p.show_unused_check.toggled.connect(lambda _: self.redraw())
        p.spectra_tree.itemChanged.connect(self._spectrum_ticked)
        p.spectrum_property_combo.currentIndexChanged.connect(lambda _: self.redraw_spectra())
        p.spectrum_baseline_combo.currentIndexChanged.connect(lambda _: self.redraw_spectra())
        p.hv_limit_check.toggled.connect(self._hv_toggled)
        p.hv_limit_spin.valueChanged.connect(lambda _: self.redraw_spectra())
        p.mark_kinetics_check.toggled.connect(lambda _: self.redraw_spectra())
        p.remove_spectrum_button.clicked.connect(self.remove_spectrum)
        w.actions["open_folder"].triggered.connect(self.open_folder)
        w.actions["add_files"].triggered.connect(self.add_files)
        w.actions["example"].triggered.connect(self.load_example)
        w.actions["clear"].triggered.connect(self.clear_all)
        app.signals.filesChanged.connect(self.refresh)
        app.signals.processingChanged.connect(self.redraw)
        app.signals.settingsReplaced.connect(self.refresh)

    # ------------------------------------------------------------------ window state (project)
    def view_state(self):
        p = self.panel
        return {"show_unused_traces": p.show_unused_check.isChecked(),
                "spectrum_property": p.spectrum_property_combo.currentData(),
                "spectrum_baseline": p.spectrum_baseline_combo.currentData(),
                "spectrum_hv_limit": p.hv_limit_check.isChecked(),
                "spectrum_hv_max": p.hv_limit_spin.value(),
                "spectrum_mark_kinetics": p.mark_kinetics_check.isChecked()}

    def apply_view_state(self, st):
        p = self.panel
        p.show_unused_check.setChecked(bool(st.get("show_unused_traces", False)))
        p.hv_limit_check.setChecked(bool(st.get("spectrum_hv_limit", True)))
        p.hv_limit_spin.setValue(int(st.get("spectrum_hv_max", 900)))
        p.mark_kinetics_check.setChecked(bool(st.get("spectrum_mark_kinetics", True)))
        self._wanted = {"property": st.get("spectrum_property"), "baseline": st.get("spectrum_baseline")}
        self.refresh_spectra()

    # ------------------------------------------------------------------ loading
    def open_folder(self):
        d = QFileDialog.getExistingDirectory(self.app.window, "Folder with Chirascan files (*.csv, *.dsx)",
                                             self.app.last_dir())
        if d:
            self.add_paths([d])

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self.app.window, "Chirascan files", self.app.last_dir(),
            "Chirascan files (*.csv *.dsx);;CSV export (*.csv);;Chirascan binary (*.dsx);;All files (*)")
        if paths:
            self.add_paths(paths)

    def load_example(self):
        self.add_paths([example_path("TT3T-10K00000.csv")], remember_dir=False)

    def add_paths(self, paths, remember_dir=True):
        files, errors = [], []
        for p in paths:
            if os.path.isdir(p):
                try:
                    files += data_files_in(p)
                except FileNotFoundError as exc:
                    errors.append(str(exc))
            elif os.path.isfile(p):
                files.append(p)
        added, read_errors = self.session.add_files(files)
        errors += read_errors
        if remember_dir and paths:
            self.app.set_last_dir(paths[0])
        if added:
            n_k, n_s = self.session.last_added["kinetics"], self.session.last_added["spectra"]
            self.app.signals.filesChanged.emit()
            self.app.recompute()
            self.app.window.show_plot("raw" if n_k or not n_s else "spectra")
            parts = ([f"{n_k} kinetics file(s)"] if n_k else []) + ([f"{n_s} spectrum/spectra"] if n_s else [])
            self.app.status(" and ".join(parts) + " loaded.")
        elif files and not errors:
            self.app.status("These files are already loaded.")
        if errors:
            self.app.error("Loading files", "\n\n".join(errors))

    def remove_selected(self):
        rows = self.panel.files_table.selectionModel().selectedRows()
        if not rows:
            self.app.status("Select a file in the table first.")
            return
        idx = rows[0].row()
        name = self.session.files[idx].name
        self.session.remove_file(idx)
        self.app.signals.filesChanged.emit()
        self.app.recompute()
        self.app.status(f"{name} removed.")

    def remove_spectrum(self):
        item = self.panel.spectra_tree.currentItem()
        if item is None:
            self.app.status("Select a spectrum in the list first.")
            return
        idx = item.data(0, Qt.UserRole)
        name = self.session.spectra[idx].name
        self.session.remove_spectrum(idx)
        self.refresh_spectra()
        self.app.status(f"{name} removed.")

    def clear_all(self):
        if not self.session.files and not self.session.spectra:
            return
        if QMessageBox.question(self.app.window, "Close all data",
                                "Remove all files, spectra, fits and F-tests?") != QMessageBox.Yes:
            return
        specs, f_defs = self.session.specs, self.session.f_test_defs
        self.session.clear()
        self.session.specs, self.session.f_test_defs = specs, f_defs   # keep the user's p0
        self.app.signals.filesChanged.emit()
        self.app.recompute()
        self.app.signals.fitsChanged.emit()
        self.app.signals.ftestsChanged.emit()
        self.app.status("All data removed.")

    # ------------------------------------------------------------------ views
    def refresh(self):
        s = self.session
        t = self.panel.files_table
        t.setRowCount(len(s.files))
        for r, kf in enumerate(s.files):
            md = kf.metadata
            values = [kf.name, md["Measurement date"], md["Temperature"], md["Pathlength (mm)"],
                      md["Wavelength (nm)"], md["Bandwidth (nm)"], str(len(kf.traces))]
            for c, v in enumerate(values):
                item = QTableWidgetItem("" if v is None else str(v))
                if c == 0:
                    item.setIcon(icons.get(kf.fmt))
                    item.setToolTip(kf.path)
                t.setItem(r, c, item)
        tree = self.panel.traces_tree
        tree.blockSignals(True)
        tree.clear()
        chosen = set(s.settings.chosen_columns)
        for i, kf in enumerate(s.files):
            top = QTreeWidgetItem([f"{i + 1}: {kf.name}", str(len(kf.data)), ""])
            top.setIcon(0, icons.get(kf.fmt))
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            top.setData(0, Qt.UserRole, (i, None))
            for col in kf.traces:
                ch = QTreeWidgetItem([col, str(len(kf.data)), f"{kf.data[col].mean():.3f}"])
                ch.setIcon(0, icons.get("raw"))
                ch.setFlags(ch.flags() | Qt.ItemIsUserCheckable)
                ch.setCheckState(0, Qt.Checked if (i, col) in chosen else Qt.Unchecked)
                ch.setData(0, Qt.UserRole, (i, col))
                top.addChild(ch)
            tree.addTopLevelItem(top)
            top.setExpanded(True)
        tree.blockSignals(False)
        self._update_selection_label()
        self.redraw()
        self.refresh_spectra()

    # ------------------------------------------------------------------ spectra
    def refresh_spectra(self):
        """List of the spectra, the choice of property and baseline, then the plot."""
        s, p = self.session, self.panel
        tree = p.spectra_tree
        tree.blockSignals(True)
        tree.clear()
        for i, sp in enumerate(s.spectra):
            md = sp.metadata
            item = QTreeWidgetItem([sp.stem, sp.range_text, md.get("Temperature") or "",
                                    md.get("Measurement date") or ""])
            item.setIcon(0, icons.get("spectrum"))
            item.setToolTip(0, f"{sp.path}\n{sp.n_scans} scan(s); {', '.join(sp.properties)}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if sp.visible else Qt.Unchecked)
            item.setData(0, Qt.UserRole, i)
            tree.addTopLevelItem(item)
        tree.blockSignals(False)

        wanted = getattr(self, "_wanted", None) or {}
        self._wanted = None
        combo = p.spectrum_property_combo
        prev = wanted.get("property") or combo.currentData() or "CircularDichroism"
        props = []
        for sp in s.spectra:
            props += [q for q in sp.properties if q not in props]
        combo.blockSignals(True)
        combo.clear()
        for q in props:
            combo.addItem(PROPERTY_NAMES.get(q, q), q)
        i = combo.findData(prev)
        combo.setCurrentIndex(i if i >= 0 else 0)
        combo.blockSignals(False)

        combo = p.spectrum_baseline_combo
        prev = wanted.get("baseline") if "baseline" in wanted else combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("nothing", None)
        for sp in s.spectra:
            combo.addItem(icons.get("spectrum"), sp.stem, sp.path)
        i = combo.findData(prev)
        combo.setCurrentIndex(i if i >= 0 else 0)
        combo.blockSignals(False)
        for w in (p.spectrum_property_combo, p.spectrum_baseline_combo, p.remove_spectrum_button):
            w.setEnabled(bool(s.spectra))
        self.redraw_spectra()

    def _spectrum_ticked(self, item, column):
        idx = item.data(0, Qt.UserRole)
        if idx is not None and idx < len(self.session.spectra):
            self.session.spectra[idx].visible = item.checkState(0) == Qt.Checked
            self.redraw_spectra()

    def _hv_toggled(self, on):
        self.panel.hv_limit_spin.setEnabled(on)
        self.redraw_spectra()

    def spectra_plot_options(self):
        """What the plot 'Spectra' shows (also used by the Excel export)."""
        p, s = self.panel, self.session
        base_path = p.spectrum_baseline_combo.currentData()
        baseline = next((sp for sp in s.spectra if sp.path == base_path), None)
        kin_wl = []
        if p.mark_kinetics_check.isChecked():
            for kf in s.files:
                try:
                    kin_wl.append(float(kf.metadata.get("Wavelength (nm)")))
                except (TypeError, ValueError):
                    pass
        return {"items": [sp for sp in s.spectra if sp.visible],
                "prop": p.spectrum_property_combo.currentData() or "CircularDichroism",
                "baseline": baseline, "kinetics_wavelengths": kin_wl,
                "hv_max": float(p.hv_limit_spin.value()) if p.hv_limit_check.isChecked() else None}

    def redraw_spectra(self):
        panel = self.app.window.plots["spectra"]
        figures.spectra(panel.figure, **self.spectra_plot_options())
        panel.redraw()

    def _update_selection_label(self):
        n = len(self.session.settings.chosen_columns)
        total = sum(len(f.traces) for f in self.session.files)
        self.panel.selection_label.setText(f"{n} of {total} traces selected." if total else "")

    def redraw(self):
        s = self.session
        panel = self.app.window.plots["raw"]
        figures.raw_traces(panel.figure, s.files, s.settings.chosen_columns,
                           show_unused=self.panel.show_unused_check.isChecked())
        panel.redraw()

    def _tree_changed(self, item, column):
        tree = self.panel.traces_tree
        chosen = []
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            for j in range(top.childCount()):
                ch = top.child(j)
                if ch.checkState(0) == Qt.Checked:
                    chosen.append(tuple(ch.data(0, Qt.UserRole)))
        if chosen == self.session.settings.chosen_columns:
            return
        self.session.settings.chosen_columns = chosen
        self._update_selection_label()
        self.app.recompute()

    def _check_all(self, state):
        tree = self.panel.traces_tree
        tree.blockSignals(True)
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            for j in range(top.childCount()):
                top.child(j).setCheckState(0, Qt.Checked if state else Qt.Unchecked)
        tree.blockSignals(False)
        self._tree_changed(None, 0)
