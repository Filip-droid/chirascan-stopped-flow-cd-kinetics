# src/views/dialogs/help_dialogs.py
"""The quick-help window of the orange "?" buttons and the help search
window (F1)."""

import html

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QPushButton, QTextBrowser, QVBoxLayout)

from src.views import icons

QUICK_CSS = ("body { font-family: 'Segoe UI'; font-size: 10pt; } code { background:#F1F4F8; }"
             "h3 { color:#1F5FA8; margin:0 0 6px 0; }")


class QuickHelpDialog(QDialog):
    """Short help with a button to the full help section."""
    fullHelpRequested = pyqtSignal(str, str)

    def __init__(self, title, page, anchor, body, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Quick help – {title}")
        self.setWindowIcon(icons.get("quick_help"))
        self.resize(480, 300)
        lay = QVBoxLayout(self)
        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(icons.get("quick_help").pixmap(32, 32))
        head.addWidget(ic)
        t = QLabel(f"<b style='font-size:12pt;color:#1F5FA8'>{html.escape(title)}</b>")
        head.addWidget(t, 1)
        lay.addLayout(head)
        self.browser = QTextBrowser()
        self.browser.document().setDefaultStyleSheet(QUICK_CSS)
        self.browser.setHtml(body)
        self.browser.setOpenExternalLinks(True)
        lay.addWidget(self.browser, 1)
        row = QHBoxLayout()
        full = QPushButton(icons.get("book"), "Full help…")
        full.setToolTip("Open this topic in the user guide (web browser)")
        full.clicked.connect(lambda: self.fullHelpRequested.emit(page, anchor))
        close = QPushButton(icons.get("exit"), "Close")
        close.clicked.connect(self.close)
        close.setDefault(True)
        row.addWidget(full)
        row.addStretch(1)
        row.addWidget(close)
        lay.addLayout(row)


class HelpSearchDialog(QDialog):
    """Search in all help pages; a double-click (or Enter) opens the hit."""
    openRequested = pyqtSignal(str, object)

    def __init__(self, search_fn, parent=None):
        super().__init__(parent)
        self._search = search_fn
        self.setWindowTitle("Search the help")
        self.setWindowIcon(icons.get("search"))
        self.resize(640, 480)
        lay = QVBoxLayout(self)
        row = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(icons.get("search").pixmap(24, 24))
        row.addWidget(ic)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Type words to find, e.g. 'path length', 'half-life', 'Durbin'…")
        self.edit.setClearButtonEnabled(True)
        row.addWidget(self.edit, 1)
        lay.addLayout(row)
        self.count = QLabel("")
        self.count.setObjectName("hint")
        lay.addWidget(self.count)
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setIconSize(QSize(20, 20))
        self.list.setAlternatingRowColors(True)
        lay.addWidget(self.list, 1)
        buttons = QHBoxLayout()
        self.open_button = QPushButton(icons.get("book"), "Open")
        self.open_button.setEnabled(False)
        close = QPushButton(icons.get("exit"), "Close")
        buttons.addStretch(1)
        buttons.addWidget(self.open_button)
        buttons.addWidget(close)
        lay.addLayout(buttons)

        self.edit.textChanged.connect(self._update)
        self.edit.returnPressed.connect(self._open_current)
        self.list.itemActivated.connect(lambda _: self._open_current())
        self.list.currentRowChanged.connect(lambda r: self.open_button.setEnabled(r >= 0))
        self.open_button.clicked.connect(self._open_current)
        close.clicked.connect(self.close)

    def _update(self, text):
        self.list.clear()
        hits = self._search(text) if text.strip() else []
        for h in hits:
            heading = h["heading"] or h["title"]
            item = QListWidgetItem(icons.get("quick_help" if h["title"] == "Quick help" else "book"),
                                   f"{heading}   —   {h['title']}\n{h['snippet']}")
            item.setData(Qt.UserRole, (h["key"], h["anchor"]))
            item.setToolTip(h["snippet"])
            self.list.addItem(item)
        self.count.setText("" if not text.strip() else f"{len(hits)} section(s) found")
        if hits:
            self.list.setCurrentRow(0)

    def _open_current(self):
        item = self.list.currentItem()
        if item is not None:
            key, anchor = item.data(Qt.UserRole)
            self.openRequested.emit(key, anchor)
