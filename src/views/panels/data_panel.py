# src/views/panels/data_panel.py
"""Step 1 - Data: loading of the Chirascan CSV files, their metadata and the
choice of the traces (repeats) to average."""

from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QGridLayout, QHBoxLayout, QHeaderView, QTableWidget,
                             QTreeWidget, QVBoxLayout, QWidget)

from src.views.widgets import button, help_group, hint

METADATA_HEADERS = ["File", "Date", "Temperature", "Path (mm)", "λ (nm)", "Bandwidth (nm)", "Traces"]


class DataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)

        box, c = help_group("Input files", "files")
        grid = QGridLayout()
        self.open_folder_button = button("Open folder…", "open_folder",
                                         "Load every Chirascan CSV file of a folder (Ctrl+O)")
        self.add_files_button = button("Add CSV files…", "add_files", "Add one or more CSV files (Ctrl+Shift+O)")
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
        self.files_table.setMinimumHeight(110)
        c.addWidget(self.files_table)
        c.addWidget(hint("Tip: you can also drag CSV files or a folder from Explorer onto the window."))
        lay.addWidget(box)

        box2, c2 = help_group("Traces to average", "traces")
        self.traces_tree = QTreeWidget()
        self.traces_tree.setHeaderLabels(["Trace", "Points", "Mean (mdeg)"])
        self.traces_tree.setColumnCount(3)
        self.traces_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.traces_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.traces_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.traces_tree.header().setStretchLastSection(False)
        self.traces_tree.setMinimumHeight(150)
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
        c2.addWidget(hint("Untick repeats that are clearly wrong (air bubble, failed shot); they disappear from the "
                          "plot. The ticked traces are averaged; the time axis of the first ticked trace is used."))
        self.selection_label = hint("")
        c2.addWidget(self.selection_label)
        lay.addWidget(box2, 1)
