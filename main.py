# main.py
"""StoppedFlowKinetiX - analysis of stopped-flow CD kinetics (Chirascan).

Start:  python main.py [project.sfkx | data.csv | folder ...]

The top level stays light (only the standard library) so that a missing
package can be reported in a message box instead of an unreadable traceback
(in the --windowed PyInstaller build there is no console to print it to)."""

import importlib.util
import os
import sys

_REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("xlsxwriter", "xlsxwriter"),
]


def _missing_required_packages():
    return [(imp, pip) for imp, pip in _REQUIRED_PACKAGES if importlib.util.find_spec(imp) is None]


def _fail_with_missing_packages(missing):
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
    lines = "\n".join(f"  • {imp}  (pip install {pkg})" for imp, pkg in missing)
    QMessageBox.critical(None, "Missing required packages",
                         "StoppedFlowKinetiX cannot start because these Python packages are not installed:\n\n"
                         f"{lines}\n\nInstall everything with:\n\n    pip install -r requirements.txt")
    sys.exit(1)


def _install_excepthook():
    """Unexpected errors: logged and shown in a message box instead of closing the program."""
    import traceback

    from src.modules.utils.app_logger import get_logger
    logger = get_logger("unhandled")

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        logger.error("Unhandled exception:\n%s", text)
        try:
            from PyQt5.QtWidgets import QMessageBox
            box = QMessageBox(QMessageBox.Critical, "Unexpected error",
                              f"{exc_type.__name__}: {exc}\n\nThe program keeps running; the details are in the "
                              f"log (Help › Open log file).")
            box.setDetailedText(text)
            box.exec_()
        except Exception:                      # noqa: BLE001
            pass
    sys.excepthook = hook


def main():
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    missing = _missing_required_packages()
    if missing:
        _fail_with_missing_packages(missing)

    import matplotlib
    matplotlib.use("Qt5Agg")

    from src.modules.utils.app_logger import get_logger, setup_logging
    from src.version import APP_NAME, APP_VERSION
    setup_logging()
    _install_excepthook()
    get_logger(__name__).info("%s %s starting", APP_NAME, APP_VERSION)

    if sys.platform == "win32":                # own taskbar icon instead of python.exe's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"IBP.{APP_NAME}.{APP_VERSION}")
        except Exception:                      # noqa: BLE001
            pass

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)

    from src.views import icons, theme
    theme.apply(app)
    app.setWindowIcon(icons.get("app"))

    from src.controllers.main_controller import MainController
    controller = MainController(open_paths=[a for a in sys.argv[1:] if os.path.exists(a)])
    controller.show()
    controller.autosave.start()          # automatic saving; offers to restore work after a crash
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
