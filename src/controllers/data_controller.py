# src/controllers/data_controller.py
"""Step 1 - loading the files and choosing the traces."""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QTreeWidgetItem

from src.modules.data_io.chirascan_reader import csv_files_in
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
        w.actions["open_folder"].triggered.connect(self.open_folder)
        w.actions["add_files"].triggered.connect(self.add_files)
        w.actions["example"].triggered.connect(self.load_example)
        w.actions["clear"].triggered.connect(self.clear_all)
        app.signals.filesChanged.connect(self.refresh)
        app.signals.processingChanged.connect(self.redraw)
        app.signals.settingsReplaced.connect(self.refresh)

    # ------------------------------------------------------------------ window state (project)
    def view_state(self):
        return {"show_unused_traces": self.panel.show_unused_check.isChecked()}

    def apply_view_state(self, st):
        self.panel.show_unused_check.setChecked(bool(st.get("show_unused_traces", False)))

    # ------------------------------------------------------------------ loading
    def open_folder(self):
        d = QFileDialog.getExistingDirectory(self.app.window, "Folder with Chirascan CSV files", self.app.last_dir())
        if d:
            self.add_paths([d])

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self.app.window, "Chirascan CSV files", self.app.last_dir(),
                                                "CSV files (*.csv);;All files (*)")
        if paths:
            self.add_paths(paths)

    def load_example(self):
        self.add_paths([example_path("TT3T-10K00000.csv")], remember_dir=False)

    def add_paths(self, paths, remember_dir=True):
        files, errors = [], []
        for p in paths:
            if os.path.isdir(p):
                try:
                    files += csv_files_in(p)
                except FileNotFoundError as exc:
                    errors.append(str(exc))
            elif os.path.isfile(p):
                files.append(p)
        added, read_errors = self.session.add_files(files)
        errors += read_errors
        if remember_dir and paths:
            self.app.set_last_dir(paths[0])
        if added:
            self.app.signals.filesChanged.emit()
            self.app.recompute()
            self.app.window.show_plot("raw")
            self.app.status(f"{added} file(s) loaded.")
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

    def clear_all(self):
        if not self.session.files:
            return
        if QMessageBox.question(self.app.window, "Close all data",
                                "Remove all files, fits and F-tests?") != QMessageBox.Yes:
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
                    item.setIcon(icons.get("csv"))
                    item.setToolTip(kf.path)
                t.setItem(r, c, item)
        tree = self.panel.traces_tree
        tree.blockSignals(True)
        tree.clear()
        chosen = set(s.settings.chosen_columns)
        for i, kf in enumerate(s.files):
            top = QTreeWidgetItem([f"{i + 1}: {kf.name}", str(len(kf.data)), ""])
            top.setIcon(0, icons.get("csv"))
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
