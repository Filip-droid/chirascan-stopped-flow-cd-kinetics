# src/controllers/autosave_controller.py
"""Automatic saving with crash recovery (as in SpecAnalytiXBase).

Automatic saving
    Every few minutes (File › Automatic saving: off / 2 / 5 / 10 / 20 min,
    remembered between sessions) the whole analysis - the same content as a
    project file: copies of the CSV files, settings, p0, fits, F-tests,
    report, window state - is saved into the per-user autosave folder, only
    when something changed since the last automatic save. It waits while a
    fit is running; the file is written on a background thread, atomically.
    The status bar shows "Saved automatically at …".

Crash recovery
    start() is called once the main window is shown (main.py). If an earlier
    instance ended without closing normally and left an automatic save, the
    user is asked: Restore / Discard / Not now. A normal close removes this
    instance's files (shutdown()), so only abnormal endings are offered.

It does not replace File › Save project: the automatic save is deleted when
the program is closed normally."""

import datetime
import hashlib
import threading
import time

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu, QMessageBox

from src.modules.core.session import read_state_file, write_state_file
from src.modules.utils.app_logger import get_logger
from src.modules.utils.session_files import AUTOSAVE_CHOICES, DEFAULT_AUTOSAVE_MINUTES, AutosaveManager
from src.version import APP_NAME, APP_VERSION
from src.views import icons

logger = get_logger(__name__)
BUSY_RETRY_SECONDS = 20


class AutosaveController(QObject):
    def __init__(self, app, manager=None):
        super().__init__()
        self.app = app
        self.manager = manager or AutosaveManager()
        self.started = False
        self.last_saved_at = None
        self.last_duration = 0.0
        self._last_hash = None
        self._writer = None
        self._write_error = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.autosave_now)
        self._retry = QTimer(self)
        self._retry.setSingleShot(True)
        self._retry.timeout.connect(self.autosave_now)
        self._watch = QTimer(self)
        self._watch.timeout.connect(self._check_writer)
        self._build_menu()

    # ------------------------------------------------------------------ settings
    def minutes(self):
        v = self.app.settings.value("autosave_minutes", DEFAULT_AUTOSAVE_MINUTES, type=int)
        return v if v in AUTOSAVE_CHOICES else DEFAULT_AUTOSAVE_MINUTES

    def set_interval(self, minutes):
        self.app.settings.setValue("autosave_minutes", minutes)
        self._apply_interval(minutes)

    def _apply_interval(self, minutes):
        for a in self._interval_actions:
            a.setChecked(a.data() == minutes)
        if minutes and self.started:
            self.timer.start(int(minutes * 60 * 1000))
        else:
            self.timer.stop()
            if self.started and not minutes:
                self.wait_for_write(30)
                self.manager.remove_autosave()
                self._last_hash = None

    # ------------------------------------------------------------------ lifecycle
    def start(self, offer_recovery=True):
        try:
            self.manager.start_session(APP_VERSION)
        except OSError as exc:
            logger.warning("Automatic saving unavailable (%s)", exc)
            return
        self.started = True
        self._apply_interval(self.minutes())
        if offer_recovery:
            QTimer.singleShot(600, self.offer_recovery)

    def shutdown(self):
        """Normal exit: nothing of this session needs recovering."""
        self.timer.stop()
        self._retry.stop()
        self._watch.stop()
        self.wait_for_write(30)
        if self.started:
            self.manager.end_session()
            self.started = False

    # ------------------------------------------------------------------ saving
    def _busy(self):
        return self.app.fit.runner.busy or self.app.compare.runner.busy

    def autosave_now(self, force=False):
        """Save if anything changed. Returns True when a save was started."""
        if not self.started or self.is_writing():
            return False
        if not force and self._busy():
            self._retry.start(BUSY_RETRY_SECONDS * 1000)
            return False
        s = self.app.session
        if not s.files:
            self.manager.remove_autosave()          # nothing to recover
            self._last_hash = None
            return False
        report = self.app.window.results_panel.report.toPlainText()
        digest = hashlib.sha1((s.signature() + report).encode("utf-8")).hexdigest()
        if digest == self._last_hash:
            return False
        try:
            state = s.build_state(report_text=report, view_state=self.app.view_state())
            state["autosave"] = {"project_path": s.project_path, "unsaved": s.has_unsaved_changes,
                                 "saved_at": datetime.datetime.now().isoformat(timespec="seconds")}
        except Exception:                           # noqa: BLE001
            logger.exception("Automatic save: could not collect the state")
            return False
        path = self.manager.autosave_path()
        self._show_status("Saving automatically…", 0)

        def write():
            t0 = time.perf_counter()
            try:
                write_state_file(path, state)
                self._last_hash = digest
                self.last_saved_at = datetime.datetime.now()
                self.last_duration = time.perf_counter() - t0
                self._write_error = None
            except Exception as exc:                # noqa: BLE001 - disk full, folder removed, ...
                self._write_error = exc
                logger.warning("Automatic save failed: %s", exc)

        self._writer = threading.Thread(target=write, name="autosave", daemon=True)
        self._writer.start()
        self._watch.start(300)
        return True

    def is_writing(self):
        return self._writer is not None and self._writer.is_alive()

    def wait_for_write(self, timeout=None):
        if self._writer is not None:
            self._writer.join(timeout)

    def _check_writer(self):
        if self.is_writing():
            return
        self._watch.stop()
        if self._write_error is not None:
            self._show_status("Automatic save failed (see the log)", 15000)
        elif self.last_saved_at is not None:
            note = f" ({self.last_duration:.0f} s)" if self.last_duration >= 2 else ""
            self._show_status(f"Saved automatically at {self.last_saved_at:%H:%M}{note}", 8000)

    def _show_status(self, text, timeout_ms):
        try:
            self.app.window.statusBar().showMessage(text, timeout_ms)
        except RuntimeError:
            pass

    # ------------------------------------------------------------------ recovery
    def offer_recovery(self):
        """Ask about each session that ended abnormally. Returns 1 if one was restored."""
        for found in self.manager.find_recoverable():
            saved = datetime.datetime.fromtimestamp(found["saved_at"])
            box = QMessageBox(self.app.window)
            box.setWindowTitle("Restore unsaved work?")
            box.setIconPixmap(icons.get("refresh").pixmap(40, 40))
            box.setText(f"<b>{APP_NAME} was not closed normally last time</b> (for example a crash or a "
                        f"power cut).")
            box.setInformativeText(
                f"Your work was saved automatically on {saved:%d %b %Y at %H:%M} "
                f"({found['size'] / 1e6:.1f} MB). Restore it now?\n\n"
                "Restore: open it as it was.\nDiscard: delete it.\nNot now: keep it and ask again next time.")
            restore = box.addButton("Restore", QMessageBox.AcceptRole)
            restore.setIcon(icons.get("refresh"))
            discard = box.addButton("Discard", QMessageBox.DestructiveRole)
            discard.setIcon(icons.get("clear"))
            later = box.addButton("Not now", QMessageBox.RejectRole)
            later.setIcon(icons.get("stop"))
            box.setDefaultButton(restore)
            box.exec_()
            clicked = box.clickedButton()
            if clicked is restore:
                if self._restore(found):
                    return 1
            elif clicked is discard:
                self.manager.discard(found)
        return 0

    def _restore(self, found):
        s = self.app.session
        try:
            state = read_state_file(found["path"])
            errors = s.load_state(state)
        except Exception as exc:                    # noqa: BLE001
            QMessageBox.warning(self.app.window, "Could not restore",
                                f"The automatically saved work could not be opened ({exc}). It has been kept, "
                                f"in case it can be opened later:\n{found['path']}")
            return False
        info = state.get("autosave", {})
        s.project_path = info.get("project_path")
        s.saved_signature = ""                      # restored work counts as unsaved
        self.app.refresh_after_load(errors, "Work restored from the automatic save")
        self.manager.discard(found)
        self._last_hash = None
        self.autosave_now(force=True)               # protect it under this session
        return True

    # ------------------------------------------------------------------ menu
    def _build_menu(self):
        w = self.app.window
        menu = QMenu("Automatic saving", w)
        menu.setIcon(icons.get("save"))
        menu.aboutToShow.connect(self._update_status_action)
        self._status_action = QAction(menu)
        self._status_action.setEnabled(False)
        menu.addAction(self._status_action)
        menu.addSeparator()
        group = QActionGroup(menu)
        self._interval_actions = []
        for m in AUTOSAVE_CHOICES:
            a = QAction("Off" if m == 0 else f"Every {m} minutes", menu, checkable=True)
            a.setData(m)
            a.triggered.connect(lambda _=False, m=m: self.set_interval(m))
            group.addAction(a)
            menu.addAction(a)
            self._interval_actions.append(a)
        menu.addSeparator()
        now = QAction(icons.get("run"), "Save automatically now", menu)
        now.triggered.connect(lambda: self.autosave_now(force=True) or self._show_status(
            "Nothing changed since the last automatic save.", 5000))
        menu.addAction(now)
        about = QAction(icons.get("info"), "About automatic saving…", menu)
        about.triggered.connect(self._explain)
        menu.addAction(about)
        w.file_menu.insertMenu(w.actions["export_excel"], menu)
        w.file_menu.insertSeparator(w.actions["export_excel"])
        self.menu = menu
        self._apply_interval(self.minutes())

    def _update_status_action(self):
        if not self.minutes():
            text = "Automatic saving is off"
        elif self._write_error is not None:
            text = "The last automatic save failed (see the log)"
        elif self.last_saved_at:
            text = f"Last saved automatically at {self.last_saved_at:%H:%M}"
        else:
            text = "Nothing saved automatically yet"
        self._status_action.setText(text)

    def _explain(self):
        QMessageBox.information(
            self.app.window, "Automatic saving",
            f"While you work, {APP_NAME} saves the whole analysis - copies of the data files, all settings, "
            "fits, F-tests and the report - every few minutes, but only when something has changed.\n\n"
            "If the program ends unexpectedly (crash, power cut), you are offered to restore that work the "
            "next time you start it. When you close the program normally, the automatic save is deleted. "
            "It does not replace File › Save project.\n\n"
            f"Folder: {self.manager.folder}")
