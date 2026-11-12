# src/views/panels/data_panel.py
"""Step 1 - Data: loading of the Chirascan files (CSV export or binary .dsx),
their metadata, the choice of the traces (repeats) to average and the spectra
measured with them (shown in the plot "Spectra")."""

from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                             QLabel, QScrollArea, QSpinBox, QTableWidget, QTreeWidget, QVBoxLayout, QWidget)

from src.views.widgets import button, help_group, hint

METADATA_HEADERS = ["File", "Date", "Temperature", "Path (mm)", "λ (nm)", "Bandwidth (nm)", "Traces"]


class DataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()                  # scrolls instead of squeezing on small screens
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(6, 6, 6, 6)

        box, c = help_group("Input files", "files")
        grid = QGridLayout()
        self.open_folder_button = button("Open folder…", "open_folder",
                                         "Load every Chirascan file of a folder - kinetics and spectra, *.csv or *.dsx (Ctrl+O)")
        self.add_files_button = button("Add files…", "add_files",
                                       "Add one or more Chirascan files, *.csv or *.dsx (Ctrl+Shift+O)")
        self.example_button = button("Load example", "flask",
                                     "Load the example data (TT3T G-quadruplex, 10 mM K⁺, 4 repeats)")
        self.remove_button = button("Remove file", "remove", "Remove the file selected in the table")
        self.clear_button = button("Clear all", "clear", "Remove all files and results")
        grid.addWidget(self.open_folder_button, 0, 0)
        grid.addWidget(self.add_files_button, 0, 1)
        grid.addWidget(self.example_button, 0, 2)
        grid.addWidget(self.remove_button, 1, 0)
        grid.addWidget(self.clear_button, 1, 1)
        c.addLayout(grid)
        self.files_table = QTableWidget(0, len(METADATA_HEADERS))
        self.files_table.setHorizontalHeaderLabels(METADATA_HEADERS)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setMinimumHeight(90)
        c.addWidget(self.files_table)
        self.files_table.setToolTip("Kinetic measurements (*.csv or *.dsx). Tip: drag files or a folder onto the "
                                    "window; spectra found among them are listed under 'Spectra'.")
        lay.addWidget(box)

        box2, c2 = help_group("Traces to average", "traces")
        self.traces_tree = QTreeWidget()
        self.traces_tree.setHeaderLabels(["Trace", "Points", "Mean (mdeg)"])
        self.traces_tree.setColumnCount(3)
        self.traces_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.traces_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.traces_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.traces_tree.header().setStretchLastSection(False)
        self.traces_tree.setMinimumHeight(120)
        c2.addWidget(self.traces_tree, 1)
        row = QHBoxLayout()
        self.select_all_button = button("Select all", "check_all", "Use all traces")
        self.select_none_button = button("Select none", "check_none", "Use no trace")
        row.addWidget(self.select_all_button)
        row.addWidget(self.select_none_button)
        row.addStretch(1)
        self.show_unused_check = QCheckBox("Show unticked traces")
        self.show_unused_check.setToolTip("Draw the unticked traces faint grey and dashed in the plot 'Raw traces'")
        row.addWidget(self.show_unused_check)
        c2.addLayout(row)
        self.traces_tree.setToolTip("Untick repeats that are clearly wrong (air bubble, failed shot). The ticked "
                                    "traces are averaged on the time axis of the first one.")
        self.selection_label = hint("")
        self.selection_label.setWordWrap(False)
        c2.addWidget(self.selection_label)
        lay.addWidget(box2, 3)

        box3, c3 = help_group("Spectra", "spectra")
        self.spectra_tree = QTreeWidget()
        self.spectra_tree.setHeaderLabels(["Spectrum", "λ (nm)", "Temperature", "Date"])
        self.spectra_tree.setRootIsDecorated(False)
        self.spectra_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for k in (1, 2, 3):
            self.spectra_tree.header().setSectionResizeMode(k, QHeaderView.ResizeToContents)
        self.spectra_tree.header().setStretchLastSection(False)
        self.spectra_tree.setMinimumHeight(80)
        self.spectra_tree.setToolTip("Tick the spectra to draw in the plot 'Spectra'")
        c3.addWidget(self.spectra_tree, 1)
        g = QGridLayout()
        g.addWidget(QLabel("Show:"), 0, 0)
        self.spectrum_property_combo = QComboBox()
        self.spectrum_property_combo.setToolTip("The quantity to plot against the wavelength")
        self.spectrum_property_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        g.addWidget(self.spectrum_property_combo, 0, 1)
        g.addWidget(QLabel("Subtract:"), 0, 2)
        self.spectrum_baseline_combo = QComboBox()
        self.spectrum_baseline_combo.setToolTip("A baseline (buffer / background spectrum) subtracted from all the "
                                                "other spectra; interpolated onto their wavelengths")
        g.addWidget(self.spectrum_baseline_combo, 0, 3)
        g.setColumnStretch(3, 1)
        c3.addLayout(g)
        row3 = QHBoxLayout()
        self.hv_limit_check = QCheckBox("Hide HV >")
        self.hv_limit_check.setChecked(True)
        self.hv_limit_check.setToolTip("Leave out the wavelengths where the photomultiplier voltage (HV) is too high - "
                                       "too little light reaches the detector there (strongly absorbing sample or "
                                       "buffer) and the CD is not reliable")
        self.hv_limit_spin = QSpinBox()
        self.hv_limit_spin.setRange(100, 1200)
        self.hv_limit_spin.setSingleStep(50)
        self.hv_limit_spin.setValue(900)
        self.hv_limit_spin.setSuffix(" V")
        self.mark_kinetics_check = QCheckBox("Mark kinetics λ")
        self.mark_kinetics_check.setChecked(True)
        self.mark_kinetics_check.setToolTip("Dashed vertical lines at the wavelengths of the loaded kinetics")
        self.remove_spectrum_button = button("Remove", "remove", "Remove the spectrum selected in the list")
        row3.addWidget(self.hv_limit_check)
        row3.addWidget(self.hv_limit_spin)
        row3.addWidget(self.mark_kinetics_check)
        row3.addStretch(1)
        row3.addWidget(self.remove_spectrum_button)
        c3.addLayout(row3)
        lay.addWidget(box3, 2)
