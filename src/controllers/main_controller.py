# src/controllers/main_controller.py
"""The application controller: owns the session (model) and the main window
(view), creates the controllers of the steps and connects what belongs to the
whole program - projects, plots' copy/save, drag & drop, settings, closing."""

import os

from PyQt5.QtCore import QObject, QSettings, QStandardPaths, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QMessageBox

from src.controllers.autosave_controller import AutosaveController
from src.controllers.compare_controller import CompareController
from src.controllers.data_controller import DataController
from src.controllers.export_controller import ExportController
from src.controllers.fit_controller import FitController
from src.controllers.help_controller import HelpController
from src.controllers.processing_controller import ProcessingController
from src.modules.core.session import PROJECT_EXTENSION, AnalysisSession
from src.modules.utils.app_logger import get_logger
from src.version import APP_NAME
from src.views import icons
from src.views.main_window import MainWindow

logger = get_logger(__name__)
MAX_RECENT = 8


class AppSignals(QObject):
    filesChanged = pyqtSignal()          # files added / removed
    processingChanged = pyqtSignal()     # the averaged / converted kinetics were recomputed
    fitsChanged = pyqtSignal()           # a fit was added or replaced
    ftestsChanged = pyqtSignal()
    settingsReplaced = pyqtSignal()      # settings loaded from a project / reset: views re-read them


class MainController(QObject):
    def __init__(self, open_paths=()):
        super().__init__()
        self.session = AnalysisSession()
        self.signals = AppSignals()
        self.settings = QSettings(APP_NAME, APP_NAME)
        self.window = MainWindow()
        w = self.window

        self.data = DataController(self)
        self.processing = ProcessingController(self)
        self.fit = FitController(self)
        self.compare = CompareController(self)
        self.export = ExportController(self)
        self.help = HelpController(self)
        self.autosave = AutosaveController(self)       # started by main.py once the window is shown

        a = w.actions
        a["open_project"].triggered.connect(self.open_project)
        a["save_project"].triggered.connect(self.save_project)
        a["save_project_as"].triggered.connect(lambda: self.save_project(ask=True))
        a["exit"].triggered.connect(w.close)
        a["confirm_exit"].setChecked(self.settings.value("confirm_exit", True, type=bool))
        a["confirm_exit"].toggled.connect(lambda on: self.settings.setValue("confirm_exit", on))
        a["recompute"].triggered.connect(self.recompute)
        for i, act in enumerate(w.step_actions):
            act.triggered.connect(lambda _=False, i=i: w.step_tabs.setCurrentIndex(i))
        for act, key in zip(w.plot_actions, w.plots):
            act.triggered.connect(lambda _=False, k=key: w.show_plot(k))
        w.step_tabs.currentChanged.connect(self._step_changed)
        w.filesDropped.connect(self._dropped)
        w.closing.connect(self._closing)
        for key, panel in w.plots.items():
            panel.copyRequested.connect(lambda k=key: self.copy_plot(k))
            panel.saveRequested.connect(lambda k=key: self.save_plot(k))

        self._restore_window()
        self._update_recent_menu()
        self.recompute()
        self.signals.filesChanged.emit()
        if open_paths:
            self.open_paths(list(open_paths))

    # ------------------------------------------------------------------ common helpers
    def show(self):
        self.window.show()

    def status(self, text):
        self.window.set_status(text)
        logger.info(text)

    def error(self, title, text):
        logger.warning("%s: %s", title, text)
        QMessageBox.warning(self.window, title, text)

    def last_dir(self):
        d = self.settings.value("last_dir", "")
        if d and os.path.isdir(d):
            return d
        return QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

    def set_last_dir(self, path):
        d = path if os.path.isdir(path) else os.path.dirname(path)
        self.settings.setValue("last_dir", d)

    def recompute(self):
        self.session.recompute()
        self.signals.processingChanged.emit()
        s = self.session
        if s.result is not None:
            n = len(s.result.kinetics_df)
            self.window.data_status.setText(f"{len(s.files)} file(s) · {len(s.settings.chosen_columns)} trace(s) "
                                            f"averaged · {n} points")
        else:
            self.window.data_status.setText(f"{len(s.files)} file(s)")

    def _step_changed(self, index):
        plot = {0: "raw", 1: "trim", 2: "fit", 3: "comparison", 4: "fit"}.get(index)
        if plot:
            self.window.show_plot(plot)

    # ------------------------------------------------------------------ opening
    def open_paths(self, paths):
        """Command line / drag & drop: projects are opened, CSV files and folders added."""
        projects = [p for p in paths if p.lower().endswith(PROJECT_EXTENSION)]
        if projects:
            self.open_project(projects[0])
            return
        self.data.add_paths(paths)

    def _dropped(self, paths):
        self.open_paths(paths)

    # ------------------------------------------------------------------ projects
    def open_project(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self.window, "Open project", self.last_dir(),
                                                  f"{APP_NAME} project (*{PROJECT_EXTENSION});;All files (*)")
            if not path:
                return
        try:
            errors = self.session.load_project(path)
        except Exception as exc:              # noqa: BLE001
            self.error("Open project", f"Cannot open the project:\n{exc}")
            return
        self.set_last_dir(path)
        self._add_recent(path)
        self.refresh_after_load(errors, f"Project opened: {path}")

    def refresh_after_load(self, errors, message):
        """Views after the session was replaced (project opened, automatic save restored)."""
        self.signals.settingsReplaced.emit()
        self.signals.filesChanged.emit()
        self.recompute()
        report = self.window.results_panel.report
        report.setPlainText(self.session.report_text)
        report.verticalScrollBar().setValue(report.verticalScrollBar().maximum())
        self.signals.fitsChanged.emit()
        self.signals.ftestsChanged.emit()
        current = self.session.current_fits()
        if current:                        # show the restored fit with the lowest AIC ...
            self.fit.select_model(min(current.values(), key=lambda f: f["aic"])["model"])
            self.window.show_plot("fit")
        self.apply_view_state(self.session.view_state)    # ... unless the project says otherwise
        self._update_title()
        problems = list(errors) + list(self.session.load_notes)
        if problems:
            self.error("Open project", "\n\n".join(problems))
        n_fits = len(current)
        outdated = len(self.session.fits) - n_fits
        msg = f"{message}. {n_fits} fit(s) restored"
        if outdated:
            msg += f", {outdated} outdated (the data changed) - fit them again"
        self.status(msg + ".")

    # ------------------------------------------------------------------ state of the window
    def view_state(self):
        """What is selected and shown in the window - saved with the project."""
        w = self.window
        state = {"step": w.step_tabs.currentIndex(), "plot": w.plot_tabs.currentIndex(),
                 "results_tab": w.results_panel.currentIndex()}
        for c in (self.data, self.fit, self.compare, self.export):
            state.update(c.view_state())
        return state

    def apply_view_state(self, state):
        if not state:
            return
        w = self.window
        for c in (self.data, self.fit, self.compare, self.export):
            try:
                c.apply_view_state(state)
            except Exception as exc:          # noqa: BLE001 - an odd value must not stop the opening
                logger.warning("view state not applied: %s", exc)
        for tabs, key in ((w.step_tabs, "step"), (w.plot_tabs, "plot"), (w.results_panel, "results_tab")):
            i = state.get(key)
            if isinstance(i, int) and 0 <= i < tabs.count():
                tabs.setCurrentIndex(i)

    def save_project(self, ask=False):
        path = self.session.project_path
        if ask or not path:
            start = path or os.path.join(self.last_dir(), "stopped_flow_analysis" + PROJECT_EXTENSION)
            path, _ = QFileDialog.getSaveFileName(self.window, "Save project", start,
                                                  f"{APP_NAME} project (*{PROJECT_EXTENSION})")
            if not path:
                return False
            if not path.lower().endswith(PROJECT_EXTENSION):
                path += PROJECT_EXTENSION
        try:
            self.session.save_project(path, report_text=self.window.results_panel.report.toPlainText(),
                                      view_state=self.view_state())
        except OSError as exc:
            self.error("Save project", f"Cannot save the project:\n{exc}")
            return False
        self.set_last_dir(path)
        self._add_recent(path)
        self._update_title()
        self.status(f"Project saved: {path}")
        return True

    def _update_title(self):
        p = self.session.project_path
        base = f"{APP_NAME} – stopped-flow CD kinetics"
        self.window.setWindowTitle(f"{os.path.basename(p)} – {base}" if p else base)

    def _recent(self):
        r = self.settings.value("recent_projects", [])
        if isinstance(r, str):
            r = [r]
        return [p for p in (r or []) if os.path.isfile(p)]

    def _add_recent(self, path):
        r = [p for p in self._recent() if os.path.normcase(p) != os.path.normcase(path)]
        r.insert(0, path)
        self.settings.setValue("recent_projects", r[:MAX_RECENT])
        self._update_recent_menu()

    def _update_recent_menu(self):
        m = self.window.recent_menu
        m.clear()
        recent = self._recent()
        for p in recent:
            act = m.addAction(icons.get("open_project"), os.path.basename(p))
            act.setToolTip(p)
            act.setStatusTip(p)
            act.triggered.connect(lambda _=False, p=p: self.open_project(p))
        if not recent:
            act = m.addAction("(none)")
            act.setEnabled(False)
        else:
            m.addSeparator()
            m.addAction(icons.get("clear"), "Clear the list",
                        lambda: (self.settings.setValue("recent_projects", []), self._update_recent_menu()))

    # ------------------------------------------------------------------ plots
    def copy_plot(self, key):
        canvas = self.window.plots[key].canvas
        QGuiApplication.clipboard().setPixmap(canvas.grab())
        self.status("Plot copied to the clipboard.")

    def save_plot(self, key):
        path, _ = QFileDialog.getSaveFileName(
            self.window, "Save plot", os.path.join(self.last_dir(), f"{key}.png"),
            "PNG image (*.png);;SVG vector (*.svg);;PDF (*.pdf);;TIFF image (*.tif)")
        if not path:
            return
        try:
            self.window.plots[key].figure.savefig(path, dpi=300)
        except Exception as exc:              # noqa: BLE001
            self.error("Save plot", f"Cannot save the plot:\n{exc}")
            return
        self.set_last_dir(path)
        self.status(f"Plot saved: {path}")

    # ------------------------------------------------------------------ window state
    def _restore_window(self):
        geo = self.settings.value("geometry")
        if geo is not None:
            self.window.restoreGeometry(geo)
        state = self.settings.value("splitter")
        if state is not None:
            self.window.main_splitter.restoreState(state)

    def _confirm_close(self):
        """Ask before closing: save unsaved changes, or just confirm (unless switched off by
        the box 'Do not ask again' / File > Ask before closing). True = close."""
        unsaved = self.session.has_unsaved_changes
        ask = self.settings.value("confirm_exit", True, type=bool)
        if not unsaved and not ask:
            return True
        box = QMessageBox(self.window)
        box.setWindowTitle(f"Close {APP_NAME}")
        box.setIconPixmap(icons.get("exit").pixmap(40, 40))
        if unsaved:
            box.setText("<b>The analysis has unsaved changes.</b>")
            box.setInformativeText("Save the project (files, settings, fits, F-tests and the report) before "
                                   "closing?")
            save = box.addButton("Save and close", QMessageBox.AcceptRole)
            save.setIcon(icons.get("save"))
            discard = box.addButton("Close without saving", QMessageBox.DestructiveRole)
            discard.setIcon(icons.get("exit"))
        else:
            box.setText(f"<b>Close {APP_NAME}?</b>")
            save = None
            discard = box.addButton("Close", QMessageBox.AcceptRole)
            discard.setIcon(icons.get("exit"))
        cancel = box.addButton("Cancel", QMessageBox.RejectRole)
        cancel.setIcon(icons.get("stop"))
        box.setDefaultButton(cancel if not unsaved else save)
        check = None
        if not unsaved:
            check = QCheckBox("Do not ask again (File › Ask before closing turns it back on)")
            box.setCheckBox(check)
        box.exec_()
        clicked = box.clickedButton()
        if clicked is cancel or clicked is None:
            return False
        if check is not None and check.isChecked():
            self.settings.setValue("confirm_exit", False)
            self.window.actions["confirm_exit"].setChecked(False)
        if clicked is save:
            return self.save_project()
        return True

    def _closing(self, event):
        if self.fit.runner.busy or self.compare.runner.busy:
            if QMessageBox.question(self.window, "Exit", "A fit is still running. Exit anyway?") != QMessageBox.Yes:
                event.ignore()
                return
        elif not self._confirm_close():
            event.ignore()
            return
            self.fit.runner.cancel()
            self.compare.runner.cancel()
            self.fit.runner.wait(5000)
            self.compare.runner.wait(5000)
        self.settings.setValue("geometry", self.window.saveGeometry())
        self.settings.setValue("splitter", self.window.main_splitter.saveState())
        self.autosave.shutdown()                       # normal end: no automatic save is left behind
        event.accept()

