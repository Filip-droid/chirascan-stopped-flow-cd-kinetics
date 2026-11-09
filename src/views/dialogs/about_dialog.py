# src/views/dialogs/about_dialog.py
"""Help › About."""

import platform

import matplotlib
import numpy
import pandas
import scipy
from PyQt5.QtCore import PYQT_VERSION_STR, Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.version import (ANALYSIS_AUTHOR, ANALYSIS_VERSION, APP_NAME, APP_ORGANIZATION, APP_URL, APP_VERSION,
                         CONTACT_EMAIL, GUI_AUTHOR, SOURCE_DOI, SOURCE_REPOSITORY)
from src.views import icons


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setWindowIcon(icons.get("info"))
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(icons.get("app").pixmap(96, 96))
        logo.setAlignment(Qt.AlignTop)
        top.addWidget(logo)
        text = QLabel(f"""
<h2 style="color:#1F5FA8;margin-bottom:0">{APP_NAME}</h2>
<p style="margin-top:2px">Version {APP_VERSION} – analysis of stopped-flow circular dichroism kinetics
(Chirascan)</p>
<p><b>Analysis</b> (models, fitting, statistics, Excel export): {ANALYSIS_AUTHOR}, notebook
v{ANALYSIS_VERSION}<br><a href="{SOURCE_REPOSITORY}">{SOURCE_REPOSITORY}</a>
&nbsp;·&nbsp; DOI <a href="https://doi.org/{SOURCE_DOI}">{SOURCE_DOI}</a><br>
<b>Graphical interface</b>: {GUI_AUTHOR} (<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>)</p>
<p>{APP_ORGANIZATION}<br><a href="{APP_URL}">Biophysics of nucleic acids</a></p>
<p style="color:#607D8B">MIT License · Python {platform.python_version()} · PyQt {PYQT_VERSION_STR} ·
numpy {numpy.__version__} · scipy {scipy.__version__} · pandas {pandas.__version__} ·
matplotlib {matplotlib.__version__}</p>""")
        text.setWordWrap(True)
        text.setOpenExternalLinks(True)
        text.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text.setMinimumWidth(460)
        top.addWidget(text, 1)
        lay.addLayout(top)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton(icons.get("exit"), "Close")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)
