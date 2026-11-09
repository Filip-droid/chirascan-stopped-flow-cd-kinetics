# src/views/panels/compare_panel.py
"""Step 4 - Compare: interpretation guide for the model comparison and the
F-test of nested models (1 vs 2 and 2 vs 3 exponentials)."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QFormLayout, QGridLayout, QLabel, QLineEdit, QScrollArea,
                             QVBoxLayout, QWidget)

from src.modules.analysis.models import F_TESTS
from src.views import icons
from src.views.widgets import button, help_group, hint

GUIDE = """<ul style="margin-left:-20px">
<li><b>R²</b>: an increase of 0.01 or more may be considered significant.</li>
<li><b>RMSD</b>: a decrease of 10 % or more may be significant.</li>
<li><b>AIC / BIC</b>: a decrease of 2 points is evidence for the better model; 6 or more is strong
evidence.</li>
<li><b>Durbin-Watson</b> far below 2: autocorrelated residuals (systematic misfit or correlated noise) -
the confidence intervals are probably too narrow.</li>
<li>Look at the <b>residuals</b> too: a good model leaves no trend in them.</li>
</ul>"""


class ComparePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(6, 6, 6, 6)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        box, c = help_group("Model comparison", "comparison")
        g = QLabel(GUIDE)
        g.setWordWrap(True)
        c.addWidget(g)
        self.show_comparison_button = button("Show all fits", "compare",
                                             "Plot every model fitted to the current data together; the table "
                                             "'Model comparison' below lists their statistics")
        c.addWidget(self.show_comparison_button)
        lay.addWidget(box)

        box, c = help_group("F-test of nested models", "ftest")
        form = QFormLayout()
        self.ftest_combo = QComboBox()
        for name, d in F_TESTS.items():
            self.ftest_combo.addItem(icons.get("ftest"), name, name)
        self.simple_label = QLabel("")
        self.complex_label = QLabel("")
        self.p0_simple_edit = QLineEdit()
        self.p0_simple_edit.setToolTip("Initial guesses of the simpler model, separated by commas")
        self.p0_complex_edit = QLineEdit()
        self.p0_complex_edit.setToolTip("Initial guesses of the more complex model, separated by commas")
        form.addRow("Comparison:", self.ftest_combo)
        form.addRow("Simpler model:", self.simple_label)
        form.addRow("p0:", self.p0_simple_edit)
        form.addRow("More complex model:", self.complex_label)
        form.addRow("p0:", self.p0_complex_edit)
        c.addLayout(form)
        c.addWidget(hint("The starting values are those of the original analysis; they can differ from the p0 of "
                         "the Fit step."))
        grid = QGridLayout()
        self.reset_ftest_button = button("Reset p0", "reset")
        self.run_ftest_button = button("Run F-test", "run", "Run the chosen comparison", primary=True)
        self.run_all_ftests_button = button("Run both", "run_all", "Run 1 vs 2 and 2 vs 3 exponentials")
        grid.addWidget(self.reset_ftest_button, 0, 0)
        grid.addWidget(self.run_ftest_button, 0, 1)
        grid.addWidget(self.run_all_ftests_button, 0, 2)
        c.addLayout(grid)
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        c.addWidget(self.result_label)
        lay.addWidget(box)
        lay.addStretch(1)
