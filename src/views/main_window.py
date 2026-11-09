# src/views/main_window.py
"""The main window (view only - no analysis logic): menus, toolbar, the five
step tabs on the left, the plots and the result tables on the right."""

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QLabel, QMainWindow, QMenu, QSplitter, QTabWidget, QToolBar

from src.version import APP_NAME, APP_VERSION
from src.views import icons
from src.views.panels.compare_panel import ComparePanel
from src.views.panels.data_panel import DataPanel
from src.views.panels.export_panel import ExportPanel
from src.views.panels.fit_panel import FitPanel
from src.views.panels.processing_panel import ProcessingPanel
from src.views.panels.results_panel import ResultsPanel
from src.views.plot_panel import PlotPanel

# step tab index -> (title, icon, help key)
STEPS = [("1 Data", "data", "files"), ("2 Process", "convert", "trimming"), ("3 Fit", "fit", "model"),
         ("4 Compare", "ftest", "comparison"), ("5 Export", "excel", "excel")]
# plot key -> (title, icon)
PLOTS = [("raw", "Raw traces", "raw"), ("average", "Average", "average"), ("trim", "Trimming", "trim"),
         ("converted", "Δε kinetics", "convert"), ("fit", "Fit && residuals", "fit"),
         ("comparison", "All fits", "compare"), ("ftest", "F-test", "ftest")]


class MainWindow(QMainWindow):
    filesDropped = pyqtSignal(list)
    closing = pyqtSignal(object)            # the close event (the controller may ignore it)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} – stopped-flow CD kinetics")
        self.setWindowIcon(icons.get("app"))
        self.resize(1500, 920)
        self.setAcceptDrops(True)
        self.setIconSize(QSize(22, 22))

        # ---- left: step tabs
        self.step_tabs = QTabWidget()
        self.step_tabs.setObjectName("stepTabs")
        self.step_tabs.setIconSize(QSize(18, 18))
        self.data_panel = DataPanel()
        self.processing_panel = ProcessingPanel()
        self.fit_panel = FitPanel()
        self.compare_panel = ComparePanel()
        self.export_panel = ExportPanel()
        for panel, (title, icon, _) in zip((self.data_panel, self.processing_panel, self.fit_panel,
                                            self.compare_panel, self.export_panel), STEPS):
            self.step_tabs.addTab(panel, icons.get(icon), title)
        self.step_tabs.setMinimumWidth(470)
        self.step_tabs.setUsesScrollButtons(False)

        # ---- right: plots over results
        self.plot_tabs = QTabWidget()
        self.plot_tabs.setObjectName("plotTabs")
        self.plot_tabs.setIconSize(QSize(18, 18))
        self.plots = {}
        for key, title, icon in PLOTS:
            panel = PlotPanel()
            self.plots[key] = panel
            self.plot_tabs.addTab(panel, icons.get(icon), title)
        self.results_panel = ResultsPanel()

        right = QSplitter(Qt.Vertical)
        right.addWidget(self.plot_tabs)
        right.addWidget(self.results_panel)
        right.setStretchFactor(0, 3)
        right.setStretchFactor(1, 1)
        right.setSizes([620, 260])

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.step_tabs)
        self.main_splitter.addWidget(right)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([500, 1000])
        self.setCentralWidget(self.main_splitter)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label, 1)
        self.data_status = QLabel("")
        self.statusBar().addPermanentWidget(self.data_status)

    # ------------------------------------------------------------------ actions
    def _action(self, key, text, icon, shortcut=None, tip=None):
        a = QAction(icons.get(icon), text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        if tip:
            a.setStatusTip(tip)
            a.setToolTip(f"{tip} ({shortcut})" if shortcut else tip)
        self.actions[key] = a
        return a

    def _create_actions(self):
        self.actions = {}
        A = self._action
        # File
        A("open_folder", "Open folder…", "open_folder", "Ctrl+O", "Load every Chirascan CSV file of a folder")
        A("add_files", "Add CSV files…", "add_files", "Ctrl+Shift+O", "Add one or more Chirascan CSV files")
        A("example", "Load example data", "flask", None, "Load the TT3T example of the original analysis")
        A("open_project", "Open project…", "open_project", "Ctrl+Shift+P", "Open a saved analysis (*.sfkx)")
        A("save_project", "Save project", "save", "Ctrl+S", "Save the files and all settings of this analysis")
        A("save_project_as", "Save project as…", "save_as", "Ctrl+Shift+S", "Save the project under a new name")
        A("export_excel", "Export to Excel…", "excel", "Ctrl+E", "Write the results workbook")
        A("export_csv", "Export data table (CSV)…", "csv", None, "Converted kinetics with fits and residuals")
        A("export_plots", "Save all plots (PNG)…", "image", None, "Save every plot as a PNG file")
        A("save_report", "Save report (TXT)…", "report", None, "Save the text report")
        A("clear", "Close all data", "clear", None, "Remove all files and results")
        A("confirm_exit", "Ask before closing", "quick_help", None,
          "Ask for confirmation when the program is closed (unsaved changes are always offered for saving)")
        self.actions["confirm_exit"].setCheckable(True)
        A("exit", "Exit", "exit", "Ctrl+Q", "Close the program")
        # Analysis
        A("recompute", "Recompute processing", "refresh", "Ctrl+R", "Average, trim and convert again")
        A("fit", "Fit the chosen model", "run", "F5", "Fit the model chosen in step 3")
        A("fit_all", "Fit all models", "run_all", "Ctrl+F5", "Fit all five models")
        A("ftests", "Run both F-tests", "ftest", "F6", "1 vs 2 and 2 vs 3 exponentials")
        A("reset_models", "Reset all model p0 and bounds", "reset", None, "Back to the original analysis values")
        # Help
        A("quick_start", "Quick start", "quick_start", None, "A five-minute walk through the program")
        A("user_guide", "User guide", "book", None, "The full manual")
        A("models_help", "Models and statistics", "fit", None, "Equations, confidence intervals, AIC/BIC, F-test")
        A("format_help", "Input data format", "csv", None, "What the Chirascan CSV export must contain")
        A("faq_help", "Troubleshooting (FAQ)", "info", None, "When a fit fails or a file does not load")
        A("search_help", "Search the help…", "search", "F1", "Find a word in all help pages")
        A("context_help", "Quick help for this step", "quick_help", "Shift+F1",
          "Short help for the step that is open")
        A("whats_new", "What's new", "whats_new", None, "Changes of this version")
        A("installation", "Installation", "install", None, "Installing and running from source")
        A("license", "License", "license", None, "The MIT license")
        A("log_file", "Open log file", "log_file", None, "The program's log (for bug reports)")
        A("about", f"About {APP_NAME}", "info", None, "Version, authors, citation")

    def _create_menus(self):
        mb = self.menuBar()
        a = self.actions
        m = mb.addMenu("&File")
        self.file_menu = m
        for k in ("open_folder", "add_files", "example", None, "open_project", "save_project", "save_project_as",
                  None):
            m.addSeparator() if k is None else m.addAction(a[k])
        self.recent_menu = QMenu("Recent projects", self)
        self.recent_menu.setIcon(icons.get("open_project"))
        m.addMenu(self.recent_menu)
        m.addSeparator()
        for k in ("export_excel", "export_csv", "export_plots", "save_report", None, "clear", None, "confirm_exit",
                  "exit"):
            m.addSeparator() if k is None else m.addAction(a[k])

        m = mb.addMenu("&Analysis")
        for k in ("recompute", None, "fit", "fit_all", "ftests", None, "reset_models"):
            m.addSeparator() if k is None else m.addAction(a[k])

        m = mb.addMenu("&View")
        self.step_actions = []
        for i, (title, icon, _) in enumerate(STEPS):
            act = QAction(icons.get(icon), f"Step {title}", self)
            act.setShortcut(QKeySequence(f"Ctrl+{i + 1}"))
            m.addAction(act)
            self.step_actions.append(act)
        m.addSeparator()
        plots_menu = m.addMenu(icons.get("fit"), "Plot")
        self.plot_actions = []
        for key, title, icon in PLOTS:
            act = QAction(icons.get(icon), title, self)
            plots_menu.addAction(act)
            self.plot_actions.append(act)

        m = mb.addMenu("&Help")
        for k in ("quick_start", "user_guide", "models_help", "format_help", "faq_help", None, "search_help",
                  "context_help", None, "whats_new", "installation", "license", "log_file", None, "about"):
            m.addSeparator() if k is None else m.addAction(a[k])

    def _create_toolbar(self):
        tb = QToolBar("Main toolbar")
        tb.setObjectName("mainToolbar")
        tb.setIconSize(QSize(24, 24))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tb.setMovable(False)
        a = self.actions
        for k in ("open_folder", "add_files", "example", None, "open_project", "save_project", None,
                  "fit", "fit_all", "ftests", None, "export_excel", None, "quick_start", "user_guide",
                  "search_help"):
            tb.addSeparator() if k is None else tb.addAction(a[k])
        # shorter texts under the icons
        short = {"open_folder": "Open folder", "add_files": "Add files", "example": "Example",
                 "open_project": "Open project", "save_project": "Save project", "fit": "Fit",
                 "fit_all": "Fit all", "ftests": "F-tests", "export_excel": "Excel", "quick_start": "Quick start",
                 "user_guide": "User guide", "search_help": "Search help"}
        for k, text in short.items():
            a[k].setIconText(text)
        self.addToolBar(tb)
        self.toolbar = tb

    # ------------------------------------------------------------------ helpers
    def show_plot(self, key):
        self.plot_tabs.setCurrentWidget(self.plots[key])

    def set_status(self, text):
        self.status_label.setText(text)

    # ------------------------------------------------------------------ drag & drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths)

    def closeEvent(self, event):
        self.closing.emit(event)
