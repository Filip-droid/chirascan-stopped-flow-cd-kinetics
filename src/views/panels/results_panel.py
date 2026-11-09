# src/views/panels/results_panel.py
"""The tables and the report under the plots: parameters of the shown fit,
statistics of all fitted models, the text report."""

from PyQt5.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QPlainTextEdit, QTableWidget,
                             QTabWidget, QToolButton, QVBoxLayout, QWidget)

from src.views import icons

COMPARISON_HEADERS = ["Model", "R²", "RMSD", "AIC", "ΔAIC", "BIC", "ΔBIC", "Durbin-Watson", "Lag-1 r",
                      "Parameters", "Warnings"]


def _table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setAlternatingRowColors(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def _tool(icon, tip):
    b = QToolButton()
    b.setIcon(icons.get(icon))
    b.setToolTip(tip)
    b.setAutoRaise(True)
    return b


class ResultsPanel(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # parameters
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        self.params_table = _table(["Parameter", "Value", "95 % CI lower", "95 % CI upper", "Unit"])
        self.stats_table = _table(["Statistic", "Value"])
        lay.addWidget(self.params_table, 3)
        lay.addWidget(self.stats_table, 2)
        side = QVBoxLayout()
        self.copy_params_button = _tool("copy", "Copy both tables to the clipboard (paste into Excel)")
        side.addWidget(self.copy_params_button)
        side.addStretch(1)
        lay.addLayout(side)
        self.addTab(w, icons.get("table"), "Fit parameters")

        # comparison
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        self.comparison_table = _table(COMPARISON_HEADERS)
        lay.addWidget(self.comparison_table, 1)
        side = QVBoxLayout()
        self.copy_comparison_button = _tool("copy", "Copy the table to the clipboard")
        side.addWidget(self.copy_comparison_button)
        side.addStretch(1)
        lay.addLayout(side)
        self.addTab(w, icons.get("compare"), "Model comparison")

        # report
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        self.report = QPlainTextEdit()
        self.report.setObjectName("report")
        self.report.setReadOnly(True)
        lay.addWidget(self.report, 1)
        side = QVBoxLayout()
        self.copy_report_button = _tool("copy", "Copy the report")
        self.save_report_button = _tool("save", "Save the report as a text file")
        self.clear_report_button = _tool("clear", "Clear the report")
        side.addWidget(self.copy_report_button)
        side.addWidget(self.save_report_button)
        side.addWidget(self.clear_report_button)
        side.addStretch(1)
        lay.addLayout(side)
        self.addTab(w, icons.get("report"), "Report")

    def append_report(self, text):
        self.report.appendPlainText(text)
        self.report.appendPlainText("")
        sb = self.report.verticalScrollBar()
        sb.setValue(sb.maximum())
