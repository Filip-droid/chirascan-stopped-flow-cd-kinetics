# src/controllers/help_controller.py
"""Help: pages in the browser, quick help of the orange "?" buttons, the help
search (F1), About, the log file."""

import os

from PyQt5.QtWidgets import QToolButton

from src.help import help_pages, help_search
from src.help.quick_help import QUICK_HELP, STEP_HELP
from src.modules.utils.app_logger import log_file_path
from src.modules.utils.system import open_with_system
from src.views.dialogs.about_dialog import AboutDialog
from src.views.dialogs.help_dialogs import HelpSearchDialog, QuickHelpDialog


class HelpController:
    def __init__(self, app):
        self.app = app
        w = app.window
        self._search_dialog = None
        self._quick = None
        a = w.actions
        for key, page in (("quick_start", "quick_start"), ("user_guide", "user_guide"), ("models_help", "models"),
                          ("format_help", "data_format"), ("faq_help", "faq"), ("whats_new", "whats_new"),
                          ("installation", "installation"), ("license", "license")):
            a[key].triggered.connect(lambda _=False, p=page: self.open_page(p))
        a["search_help"].triggered.connect(self.search)
        a["context_help"].triggered.connect(self.context_help)
        a["about"].triggered.connect(lambda: AboutDialog(w).exec_())
        a["log_file"].triggered.connect(self.open_log)
        # every orange "?" of the window
        for btn in w.findChildren(QToolButton):
            key = btn.property("helpKey")
            if key:
                btn.clicked.connect(lambda _=False, k=key: self.quick_help(k))

    def open_page(self, page, anchor=None):
        if not help_pages.open_page(page, anchor):
            self.app.error("Help", "The help page could not be opened in the web browser.\n\n"
                           f"The pages are in {help_pages.pages_dir()}")
        else:
            self.app.status(f"Help opened in the web browser: {help_pages.page_title(page)}")

    def quick_help(self, key):
        title, (page, anchor), body = QUICK_HELP[key]
        if self._quick is not None:
            self._quick.close()
        dlg = QuickHelpDialog(title, page, anchor, body, self.app.window)
        dlg.fullHelpRequested.connect(self.open_page)
        dlg.show()
        self._quick = dlg

    def context_help(self):
        self.quick_help(STEP_HELP[self.app.window.step_tabs.currentIndex()])

    def search(self):
        if self._search_dialog is None:
            self._search_dialog = HelpSearchDialog(help_search.search, self.app.window)
            self._search_dialog.openRequested.connect(self.open_page)
        self._search_dialog.show()
        self._search_dialog.raise_()
        self._search_dialog.activateWindow()
        self._search_dialog.edit.setFocus()
        self._search_dialog.edit.selectAll()

    def open_log(self):
        path = log_file_path()
        if os.path.isfile(path):
            open_with_system(path)
        else:
            self.app.status("No log file yet.")
