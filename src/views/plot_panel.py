# src/views/plot_panel.py
"""A matplotlib plot with the navigation toolbar (zoom, pan, home) and the
program's own buttons: copy to clipboard, save as image."""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from src.views import icons


class PlotPanel(QWidget):
    copyRequested = pyqtSignal()
    saveRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setIconSize(QSize(18, 18))

        self.copy_button = QToolButton()
        self.copy_button.setIcon(icons.get("copy"))
        self.copy_button.setToolTip("Copy the plot to the clipboard (paste it into Word, PowerPoint, ...)")
        self.copy_button.setAutoRaise(True)
        self.save_button = QToolButton()
        self.save_button.setIcon(icons.get("image"))
        self.save_button.setToolTip("Save the plot as an image (PNG, SVG, PDF, ...)")
        self.save_button.setAutoRaise(True)
        self.copy_button.clicked.connect(self.copyRequested)
        self.save_button.clicked.connect(self.saveRequested)

        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.addWidget(self.toolbar)
        bar.addStretch(1)
        bar.addWidget(self.copy_button)
        bar.addWidget(self.save_button)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(0)
        lay.addLayout(bar)
        lay.addWidget(self.canvas, 1)

    def redraw(self):
        self.canvas.draw_idle()
        try:
            self.toolbar.update()          # forget the old zoom history
        except Exception:                  # noqa: BLE001
            pass
