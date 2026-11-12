# src/views/theme.py
"""The look of the program: Fusion style, a light palette and a few style
sheet rules (group boxes, step tabs, the big action buttons)."""

import sys

from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QStyleFactory

ACCENT = "#1F5FA8"

STYLE_SHEET = """
QMainWindow { background: #F4F6F9; }
QGroupBox {
    font-weight: bold; border: 1px solid #CFD8DC; border-radius: 6px;
    margin-top: 12px; padding: 8px 6px 6px 6px; background: #FFFFFF;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #1F5FA8; }
QTabWidget#stepTabs::pane { border: 1px solid #CFD8DC; border-radius: 4px; background: #F9FAFC; }
QTabWidget#stepTabs QTabBar::tab {
    padding: 6px 7px; margin-right: 1px; border: 1px solid #CFD8DC; border-bottom: none;
    border-top-left-radius: 5px; border-top-right-radius: 5px; background: #E8EDF3; color: #37474F;
}
QTabWidget#stepTabs QTabBar::tab:selected { background: #FFFFFF; color: #1F5FA8; font-weight: bold; }
QTabWidget#plotTabs QTabBar::tab { padding: 5px 9px; }
QPushButton { padding: 4px 10px; }
QPushButton[primary="true"] {
    background: #E3F2FD; color: #0D3C73; font-weight: bold; border: 1px solid #1F5FA8;
    border-radius: 4px; padding: 6px 14px;
}
QPushButton[primary="true"]:hover { background: #BBDEFB; }
QPushButton[primary="true"]:pressed { background: #90CAF9; }
QPushButton[primary="true"]:disabled { background: #ECEFF1; color: #90A4AE; border-color: #CFD8DC; }
QLabel#hint { color: #607D8B; }
QLabel#factor { color: #4A148C; font-weight: bold; }
QLabel#warning { color: #B71C1C; }
QLabel#okay { color: #1B5E20; }
QPlainTextEdit#report { font-family: Consolas, Menlo, "Courier New", monospace; font-size: 9pt; background: #FFFFFF; }
QTableWidget { gridline-color: #E0E0E0; }
QHeaderView::section { background: #E8EDF3; padding: 3px; border: none; border-right: 1px solid #CFD8DC; }
QToolBar { spacing: 4px; background: #ECEFF3; border-bottom: 1px solid #CFD8DC; }
QStatusBar { background: #ECEFF3; }
"""


def apply(app):
    app.setStyle(QStyleFactory.create("Fusion"))
    if sys.platform == "win32":          # elsewhere the system font (macOS: San Francisco) is kept
        app.setFont(QFont("Segoe UI", 9))
    pal = app.palette()
    pal.setColor(QPalette.Window, QColor("#F4F6F9"))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.Link, QColor(ACCENT))
    app.setPalette(pal)
    app.setStyleSheet(STYLE_SHEET)
