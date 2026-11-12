# src/views/panels/processing_panel.py
"""Step 2 - Processing: trimming of the averaged trace, baseline subtraction
and conversion of mdeg to Δε."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
                             QSpinBox, QVBoxLayout, QWidget)

from src.modules.analysis.processing import SEQUENCE_PRESETS
from src.views import icons
from src.views.widgets import button, dspin, help_group, hint


class ProcessingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(6, 6, 6, 6)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # --- trimming
        box, c = help_group("Trimming of the averaged trace", "trimming")
        form = QFormLayout()
        self.begin_spin = QSpinBox()
        self.begin_spin.setRange(0, 100000)
        self.begin_spin.setKeyboardTracking(False)
        self.begin_spin.setToolTip("Points removed from the BEGINNING (instrument dead time)")
        self.end_spin = QSpinBox()
        self.end_spin.setRange(0, 100000)
        self.end_spin.setKeyboardTracking(False)
        self.end_spin.setToolTip("Points removed from the END (0 = keep all)")
        form.addRow("Remove from the beginning:", self.begin_spin)
        form.addRow("Remove from the end:", self.end_spin)
        c.addLayout(form)
        self.trim_label = hint("")
        c.addWidget(self.trim_label)
        lay.addWidget(box)

        # --- sample
        box, c = help_group("Sample (for the conversion to Δε)", "sample")
        form = QFormLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(icons.get("data"), "(custom)")
        for name, (n, eps) in SEQUENCE_PRESETS.items():
            self.preset_combo.addItem(icons.get("data"), f"{name}  ({n} nt, ε = {eps})", name)
        self.preset_combo.setToolTip("Sequence presets of the original analysis; fill the length and ε")
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 100000)
        self.length_spin.setSuffix(" nt")
        self.length_spin.setKeyboardTracking(False)
        self.eps_spin = dspin(0, 1e7, 1, 10, 10443, " M⁻¹cm⁻¹",
                              "Average extinction coefficient per nucleotide (M⁻¹ cm⁻¹ nt⁻¹)")
        self.absorbance_spin = dspin(0, 100, 4, 0.01, 1.6079, "",
                                     "Absorbance of the UNMIXED solution (e.g. measured on the Specord)")
        self.abs_path_spin = dspin(0.001, 100, 3, 0.1, 1.0, " cm",
                                   "Optical path length of the cuvette of the absorbance measurement")
        self.sequence_edit = QLineEdit()
        self.sequence_edit.setPlaceholderText("5'-GGGTTAGGGTTAGGGTTAGGG-3'  (optional)")
        self.sequence_edit.setClearButtonEnabled(True)
        self.sequence_edit.setToolTip(
            "Oligonucleotide sequence 5'→3': the length and ε per nucleotide are calculated from it "
            "(nearest-neighbour method, 260 nm).\nA C G T U; I = inosine (counted as G); X = abasic site "
            "(left out). Spaces, dashes and 5'/3' are ignored.")
        f = self.sequence_edit.font()
        f.setFamily("Consolas")
        self.sequence_edit.setFont(f)
        self.sequence_result = QLabel("")
        self.sequence_result.setWordWrap(False)
        self.sequence_result.setObjectName("hint")
        self.conc_source_combo = QComboBox()
        self.conc_source_combo.addItem(icons.get("convert"), "absorbance (A, sequence length, ε)", "absorbance")
        self.conc_source_combo.addItem(icons.get("convert"), "entered directly", "entered")
        self.conc_source_combo.setToolTip("How the strand concentration is obtained: from the absorbance of the "
                                          "unmixed solution, or typed in directly")
        form.addRow("Concentration from:", self.conc_source_combo)
        form.addRow("Sequence (5'→3'):", self.sequence_edit)
        form.addRow(self.sequence_result)
        form.addRow("Preset:", self.preset_combo)
        form.addRow("Sequence length:", self.length_spin)
        form.addRow("ε per nucleotide:", self.eps_spin)
        form.addRow("Absorbance (unmixed):", self.absorbance_spin)
        form.addRow("Path length (absorbance):", self.abs_path_spin)
        self.conc_spin = dspin(0.000001, 1e6, 3, 0.5, 10.0, " µM",
                               "Strand concentration (µM) - before mixing (in the syringe) or in the cell, as "
                               "chosen next to it")
        self.conc_where_combo = QComboBox()
        self.conc_where_combo.addItem("before mixing (syringe)", False)
        self.conc_where_combo.addItem("in the cell (after 1:1 mixing)", True)
        self.conc_where_combo.setToolTip("The stopped-flow mixes 1:1, so the concentration in the cell is half of "
                                         "the concentration in the syringe")
        row = QHBoxLayout()
        row.addWidget(self.conc_spin, 1)
        row.addWidget(self.conc_where_combo)
        form.addRow("Concentration:", row)
        c.addLayout(form)
        self.conc_label = QLabel("")
        self.conc_label.setObjectName("hint")
        c.addWidget(self.conc_label)
        lay.addWidget(box)

        # --- CD measurement
        box, c = help_group("CD measurement", "cd_measurement")
        form = QFormLayout()
        self.cd_path_header_check = QCheckBox("from the CSV header")
        self.cd_path_header_check.setChecked(True)
        self.cd_path_header_check.setToolTip("Use '#Pathlength:' (mm) of the selected CSV files")
        self.cd_path_spin = dspin(0.001, 100, 3, 0.1, 1.0, " cm", "Optical path length of the stopped-flow cell")
        row = QHBoxLayout()
        row.addWidget(self.cd_path_spin, 1)
        row.addWidget(self.cd_path_header_check)
        self.baseline_spin = dspin(-1e6, 1e6, 4, 0.01, 0.42, " mdeg",
                                   "Baseline: buffer (e.g. LiOH) at the same wavelength, subtracted from the signal")
        form.addRow("Path length (CD):", row)
        form.addRow("Baseline:", self.baseline_spin)
        c.addLayout(form)
        lay.addWidget(box)

        # --- result of the conversion
        box, c = help_group("Conversion", "conversion")
        form = QFormLayout()
        self.basis_combo = QComboBox()
        self.basis_combo.addItem(icons.get("convert"), "per strand (whole sequence)", "strand")
        self.basis_combo.addItem(icons.get("convert"), "per nucleotide", "nucleotide")
        self.basis_combo.setToolTip("Δε per mole of strands (whole sequence, as in the original analysis) or per "
                                    "mole of nucleotides (Δε per strand divided by the sequence length)")
        form.addRow("Δε expressed:", self.basis_combo)
        c.addLayout(form)
        self.formula_label = QLabel("")
        self.formula_label.setWordWrap(True)
        c.addWidget(self.formula_label)
        self.factor_label = QLabel("factor = –")
        self.factor_label.setObjectName("factor")
        c.addWidget(self.factor_label)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        c.addWidget(self.status_label)
        row = QHBoxLayout()
        self.reset_button = button("Reset to defaults", "reset", "The values of the original analysis (TT3T)")
        row.addWidget(self.reset_button)
        row.addStretch(1)
        c.addLayout(row)
        lay.addWidget(box)
        lay.addStretch(1)

    def set_status(self, text, ok):
        self.status_label.setObjectName("okay" if ok else "warning")
        self.status_label.setText(text)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
