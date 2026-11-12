# src/views/panels/export_panel.py
"""Step 5 - Export: the Excel workbook of the notebook, plus the data table,
the plots and the report."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QScrollArea, QVBoxLayout, QWidget)

from src.views.widgets import button, help_group, hint


class ExportPanel(QWidget):
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

        box, c = help_group("Excel workbook", "excel")
        form = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Only models fitted to the current data can be exported")
        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.browse_button = button("", "open_folder", "Choose the file name")
        self.browse_button.setFixedWidth(34)
        row.addWidget(self.path_edit, 1)
        row.addWidget(self.browse_button)
        form.addRow("Model to export:", self.model_combo)
        form.addRow("File:", row)
        c.addLayout(form)
        self.figures_check = QCheckBox("Include the fit and residual figures")
        self.figures_check.setChecked(True)
        self.open_after_check = QCheckBox("Open the workbook after export")
        self.open_after_check.setChecked(True)
        c.addWidget(self.figures_check)
        c.addWidget(self.open_after_check)
        self.export_button = button("Export to Excel", "excel", "Write the single-sheet 'Results' workbook "
                                    "(Ctrl+E)", primary=True)
        c.addWidget(self.export_button)
        c.addWidget(hint("One sheet 'Results': metadata, analysis inputs, fit results with 95 % CI, goodness of "
                         "fit, F-tests, software versions and figures on the left; the original data of the traces "
                         "used (unticked ones are left out) and the converted data with the fit and residuals on the "
                         "right."))
        lay.addWidget(box)

        box, c = help_group("Other outputs", "other_outputs")
        grid = QGridLayout()
        self.csv_button = button("Data table (CSV)…", "csv",
                                 "Converted kinetics with the fit and residuals of every fitted model")
        self.plots_button = button("All plots (PNG)…", "image", "Save every plot as a PNG image into a folder")
        self.report_button = button("Report (TXT)…", "report", "Save the text report of all fits and F-tests")
        self.project_button = button("Save project…", "save", "Save files and settings to reopen the analysis later")
        self.open_folder_button = button("Open output folder", "open_folder", "Show the folder of the workbook")
        grid.addWidget(self.csv_button, 0, 0)
        grid.addWidget(self.plots_button, 0, 1)
        grid.addWidget(self.report_button, 1, 0)
        grid.addWidget(self.project_button, 1, 1)
        grid.addWidget(self.open_folder_button, 2, 0)
        c.addLayout(grid)
        lay.addWidget(box)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        lay.addWidget(self.status_label)
        lay.addStretch(1)
