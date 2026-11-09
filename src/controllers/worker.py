# src/controllers/worker.py
"""Running the fits in the background: the window stays responsive. A task
is a list of (label, callable) steps; the result of each step is reported
when it is done, errors are reported and the next step goes on."""

import traceback

from PyQt5.QtCore import QObject, QThread, pyqtSignal


class _Worker(QObject):
    stepStarted = pyqtSignal(int, int, str)     # index, total, label
    stepDone = pyqtSignal(str, object)          # label, result
    stepFailed = pyqtSignal(str, str)           # label, message
    finished = pyqtSignal()

    def __init__(self, steps):
        super().__init__()
        self.steps = steps
        self.cancelled = False

    def run(self):
        total = len(self.steps)
        for i, (label, fn) in enumerate(self.steps):
            if self.cancelled:
                break
            self.stepStarted.emit(i, total, label)
            try:
                self.stepDone.emit(label, fn())
            except Exception as exc:            # noqa: BLE001 - every failure is reported to the user
                traceback.print_exc()
                self.stepFailed.emit(label, str(exc))
        self.finished.emit()


class TaskRunner(QObject):
    """One background task at a time."""
    stepStarted = pyqtSignal(int, int, str)
    stepDone = pyqtSignal(str, object)
    stepFailed = pyqtSignal(str, str)
    busyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None

    @property
    def busy(self):
        return self._thread is not None

    def start(self, steps):
        if self.busy:
            return False
        self._thread = QThread()
        self._worker = _Worker(steps)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.stepStarted.connect(self.stepStarted)
        self._worker.stepDone.connect(self.stepDone)
        self._worker.stepFailed.connect(self.stepFailed)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self.busyChanged.emit(True)
        self._thread.start()
        return True

    def cancel(self):
        if self._worker is not None:
            self._worker.cancelled = True

    def wait(self, ms=30000):
        if self._thread is not None:
            self._thread.wait(ms)

    def _cleanup(self):
        self._worker.deleteLater()
        self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self.busyChanged.emit(False)
