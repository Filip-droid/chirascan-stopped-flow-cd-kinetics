# src/views/panels/fit_panel.py
"""Step 3 - Fit: choice of the model, its initial guesses and bounds, the fit
options and the Fit buttons."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFormLayout, QGridLayout, QHeaderView,
                             QLabel, QScrollArea, QSpinBox, QTableWidget, QVBoxLayout, QWidget)

from src.modules.analysis.models import MODEL_NAMES
from src.views import icons
from src.views.widgets import button, help_group, hint

MODEL_ICONS = {"one phase association": "fit", "two phase association": "fit",
               "three phase association": "fit", "one phase decay": "compare", "two phase decay": "compare"}


class FitPanel(QWidget):
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

        box, c = help_group("Model", "model")
        self.model_combo = QComboBox()
        for name in MODEL_NAMES:
            self.model_combo.addItem(icons.get(MODEL_ICONS[name]), name.capitalize(), name)
        c.addWidget(self.model_combo)
        self.equation_label = QLabel("")
        self.equation_label.setWordWrap(True)
        self.equation_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.equation_label.setStyleSheet("font-family: 'Cambria Math', 'Times New Roman'; font-size: 11pt;"
                                          "color:#4A148C;")
        c.addWidget(self.equation_label)
        lay.addWidget(box)

        box, c = help_group("Initial guesses (p0), fixed parameters and bounds", "p0")
        self.p0_table = QTableWidget(0, 5)
        self.p0_table.setHorizontalHeaderLabels(["Parameter", "Fixed", "p0", "Lower", "Upper"])
        self.p0_table.horizontalHeaderItem(1).setToolTip("Tick to hold the parameter at its p0 value during the "
                                                         "fit (only the other parameters are fitted)")
        self.p0_table.verticalHeader().setVisible(False)
        self.p0_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.p0_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.p0_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.p0_table.setMinimumHeight(190)
        c.addWidget(self.p0_table)
        grid = QGridLayout()
        self.reset_p0_button = button("Reset p0", "reset", "The initial guesses and bounds of the original analysis")
        self.use_fit_button = button("Use fit as p0", "refresh",
                                     "Copy the fitted parameters of this model into p0 (to refine or to try "
                                     "small changes)")
        self.guess_button = button("Estimate p0", "zoom_fit",
                                   "Estimate the amplitudes, offset and rate constants from the data "
                                   "(fixed parameters keep their value)")
        grid.addWidget(self.reset_p0_button, 0, 0)
        grid.addWidget(self.use_fit_button, 0, 1)
        grid.addWidget(self.guess_button, 0, 2)
        c.addLayout(grid)
        c.addWidget(hint("Double-click a value to edit it; 'inf' / '-inf' = no bound. Tick 'Fixed' to keep a "
                         "parameter at its p0. A fit can depend on p0 - 'Estimate p0' searches the data for a "
                         "good start; watch the multi-start check in the report."))
        lay.addWidget(box)

        box, c = help_group("Fit options", "fit_options")
        form = QFormLayout()
        self.multistart_spin = QSpinBox()
        self.multistart_spin.setRange(0, 100)
        self.multistart_spin.setValue(5)
        self.multistart_spin.setToolTip("Randomly perturbed starting points used to check that the fit is not "
                                        "stuck in a local minimum (0 = off; seeded = reproducible)")
        self.savgol_spin = QSpinBox()
        self.savgol_spin.setRange(5, 2001)
        self.savgol_spin.setSingleStep(2)
        self.savgol_spin.setValue(51)
        self.savgol_spin.setToolTip("Window (points, odd) of the Savitzky-Golay smoothing of the residuals "
                                    "(polynomial order 3); for the plot only")
        self.auto_estimate_check = QCheckBox("Estimate p0 from the data before each fit")
        self.auto_estimate_check.setToolTip("Run 'Estimate p0' automatically when Fit or Fit all models is pressed "
                                            "(fixed parameters keep their value); the p0 used is shown in the "
                                            "table and the report")
        self.smoothed_check = QCheckBox("Show smoothed residuals")
        self.smoothed_check.setChecked(True)
        self.logx_check = QCheckBox("Logarithmic time axis")
        form.addRow("Multi-start check:", self.multistart_spin)
        form.addRow("Residual smoothing window:", self.savgol_spin)
        c.addLayout(form)
        c.addWidget(self.auto_estimate_check)
        c.addWidget(self.smoothed_check)
        c.addWidget(self.logx_check)
        lay.addWidget(box)

        box, c = help_group("Run", "run_fit")
        grid = QGridLayout()
        self.fit_button = button("Fit", "run", "Fit the chosen model (F5)", primary=True)
        self.fit_all_button = button("Fit all models", "run_all", "Fit all five models one after another (Ctrl+F5)")
        grid.addWidget(self.fit_button, 0, 0)
        grid.addWidget(self.fit_all_button, 0, 1)
        c.addLayout(grid)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        c.addWidget(self.status_label)
        lay.addWidget(box)
        lay.addStretch(1)
