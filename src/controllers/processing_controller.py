# src/controllers/processing_controller.py
"""Step 2 - trimming, sample and conversion settings."""

from PyQt5.QtCore import QTimer

from src.modules.analysis.extinction import SequenceError, extinction
from src.modules.analysis.processing import SEQUENCE_PRESETS, ProcessingSettings
from src.modules.visualization import figures


class ProcessingController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        self.panel = p = app.window.processing_panel
        self._loading = False
        self._derived = False                          # length and ε come from the sequence
        self._tips = {w: w.toolTip() for w in (p.length_spin, p.eps_spin, p.preset_combo, p.absorbance_spin,
                                                p.abs_path_spin)}
        self.load_settings()
        for w in (p.begin_spin, p.end_spin, p.length_spin):
            w.valueChanged.connect(self._changed)
        for w in (p.eps_spin, p.absorbance_spin, p.abs_path_spin, p.cd_path_spin, p.baseline_spin):
            w.valueChanged.connect(self._changed)
        p.cd_path_header_check.toggled.connect(self._changed)
        p.basis_combo.currentIndexChanged.connect(self._changed)
        p.conc_source_combo.currentIndexChanged.connect(self._changed)
        p.conc_spin.valueChanged.connect(self._changed)
        p.conc_where_combo.currentIndexChanged.connect(self._changed)
        p.preset_combo.currentIndexChanged.connect(self._preset)
        self._seq_timer = QTimer()
        self._seq_timer.setSingleShot(True)
        self._seq_timer.setInterval(300)              # calculate when typing pauses
        self._seq_timer.timeout.connect(self._sequence_changed)
        p.sequence_edit.textChanged.connect(lambda _: None if self._loading else self._seq_timer.start())
        p.sequence_edit.editingFinished.connect(self._sequence_now)
        p.reset_button.clicked.connect(self.reset)
        app.signals.processingChanged.connect(self.update_view)
        app.signals.settingsReplaced.connect(self.load_settings)

    def load_settings(self):
        """Settings of the session -> widgets."""
        s = self.session.settings
        p = self.panel
        self._loading = True
        p.begin_spin.setValue(int(s.points_from_beginning))
        p.end_spin.setValue(int(s.points_from_end))
        p.length_spin.setValue(int(s.sequence_length))
        p.eps_spin.setValue(float(s.extinction_coefficient))
        p.absorbance_spin.setValue(float(s.absorbance))
        p.abs_path_spin.setValue(float(s.absorbance_pathlength_cm))
        p.baseline_spin.setValue(float(s.baseline))
        from_header = s.cd_pathlength_cm is None
        p.cd_path_header_check.setChecked(from_header)
        p.cd_path_spin.setEnabled(not from_header)
        if not from_header:
            p.cd_path_spin.setValue(float(s.cd_pathlength_cm))
        i = p.basis_combo.findData(s.delta_eps_basis)
        p.basis_combo.setCurrentIndex(i if i >= 0 else 0)
        p.conc_source_combo.setCurrentIndex(1 if s.concentration_source == "entered" else 0)
        p.conc_spin.setValue(float(s.concentration_uM))
        p.conc_where_combo.setCurrentIndex(1 if s.concentration_in_cell else 0)
        self._show_formula()
        p.sequence_edit.setText(s.sequence or "")
        self._show_sequence(s.sequence or "")
        self._match_preset()
        self._update_enabled()
        self._loading = False

    def _update_enabled(self):
        """Which fields are used: the sequence fills length and ε; an entered concentration replaces the
        absorbance route (A, ε, path length); the length stays for Δε per nucleotide."""
        p = self.panel
        entered = p.conc_source_combo.currentData() == "entered"
        seq_tip = "Calculated from the sequence - clear the sequence to enter it yourself"
        unused_tip = "Not used - the concentration is entered directly"
        states = {
            p.length_spin: (not self._derived, seq_tip),
            p.preset_combo: (not self._derived, seq_tip),
            p.eps_spin: (not self._derived and not entered, seq_tip if self._derived else unused_tip),
            p.absorbance_spin: (not entered, unused_tip),
            p.abs_path_spin: (not entered, unused_tip),
        }
        for w, (on, off_tip) in states.items():
            w.setEnabled(on)
            w.setToolTip(self._tips[w] if on else off_tip)
        p.conc_spin.setEnabled(entered)
        p.conc_where_combo.setEnabled(entered)

    def _show_formula(self):
        p = self.panel
        per_nt = p.basis_combo.currentData() == "nucleotide"
        if p.conc_source_combo.currentData() == "entered":
            text = ("Δε = (θ − baseline) × factor,  factor = 1 / (32980 · c<sub>cell</sub> · l_CD)"
                    + (" / N" if per_nt else "") + "<br>"
                    "<span style='color:#607D8B'>c<sub>cell</sub> = strand concentration in the cell (M), "
                    "half of the concentration before mixing</span>")
        elif per_nt:
            text = ("Δε = (θ − baseline) × factor,  factor = ε·l_abs / (32980 · 0.5 · A · l_CD)<br>"
                    "<span style='color:#607D8B'>per nucleotide = per strand / N</span>")
        else:
            text = ("Δε = (θ − baseline) × factor,  factor = N·ε·l_abs / (32980 · 0.5 · A · l_CD)<br>"
                    "<span style='color:#607D8B'>per strand: N·ε is the ε of the whole sequence</span>")
        p.formula_label.setText(text)

    # ------------------------------------------------------------------ sequence -> length and ε
    def _sequence_now(self):
        if self._seq_timer.isActive():
            self._seq_timer.stop()
            self._sequence_changed()

    def _show_sequence(self, text):
        """Result label and the locking of length / ε / preset; returns the result or None."""
        p = self.panel
        res, error = None, None
        if text.strip():
            try:
                res = extinction(text)
            except SequenceError as exc:
                error = str(exc)
        self._derived = res is not None
        self._update_enabled()
        if error:
            p.sequence_result.setText(f"<span style='color:#B71C1C'>✘ {error}</span>")
            p.sequence_result.setWordWrap(True)
        elif res is None:
            p.sequence_result.setText("")
            p.sequence_result.setWordWrap(False)
        else:
            abasic = res.length - res.counted
            note = f", {abasic} abasic site(s) left out" if abasic else ""
            p.sequence_result.setWordWrap(False)
            strand = f"{res.epsilon_strand:,.0f}".replace(",", " ")
            p.sequence_result.setText(
                f"<span style='color:#1B5E20'>✔ {res.length} nt{note} · ε per nucleotide = "
                f"{res.epsilon_per_nt:.1f} M⁻¹cm⁻¹<br>&nbsp;&nbsp;&nbsp;ε of the strand = {strand} M⁻¹cm⁻¹ "
                f"(nearest-neighbour, 260 nm)</span>")
        lab = p.sequence_result
        lines = lab.text().count("<br>") + 1 if lab.text() else 0
        if lab.wordWrap() and lab.text():
            lines = max(lines, 2)
        lab.setMinimumHeight(lines * lab.fontMetrics().lineSpacing() + (4 if lines else 0))
        lab.updateGeometry()
        return res

    def _sequence_changed(self):
        if self._loading:
            return
        p = self.panel
        text = p.sequence_edit.text()
        res = self._show_sequence(text)
        if not text.strip():
            if self.session.settings.sequence:
                self.session.settings.sequence = ""
                self._changed()
            return
        if res is None:                           # invalid: keep the last values
            return
        self._loading = True
        p.length_spin.setValue(res.length)
        p.eps_spin.setValue(res.epsilon_per_nt)
        self._loading = False
        self.session.settings.sequence = res.sequence
        self._changed()

    def _match_preset(self):
        p = self.panel
        current = (p.length_spin.value(), round(p.eps_spin.value(), 1))
        p.preset_combo.blockSignals(True)
        p.preset_combo.setCurrentIndex(0)
        for i in range(1, p.preset_combo.count()):
            n, eps = SEQUENCE_PRESETS[p.preset_combo.itemData(i)]
            if (n, float(eps)) == current:
                p.preset_combo.setCurrentIndex(i)
                break
        p.preset_combo.blockSignals(False)

    def _preset(self, index):
        if index <= 0:
            return
        n, eps = SEQUENCE_PRESETS[self.panel.preset_combo.itemData(index)]
        self._loading = True
        self.panel.length_spin.setValue(n)
        self.panel.eps_spin.setValue(eps)
        self._loading = False
        self._changed()

    def _changed(self, *_):
        if self._loading:
            return
        p = self.panel
        s = self.session.settings
        s.points_from_beginning = p.begin_spin.value()
        s.points_from_end = p.end_spin.value()
        s.sequence_length = p.length_spin.value()
        s.extinction_coefficient = p.eps_spin.value()
        s.absorbance = p.absorbance_spin.value()
        s.absorbance_pathlength_cm = p.abs_path_spin.value()
        s.baseline = p.baseline_spin.value()
        from_header = p.cd_path_header_check.isChecked()
        p.cd_path_spin.setEnabled(not from_header)
        s.cd_pathlength_cm = None if from_header else p.cd_path_spin.value()
        s.delta_eps_basis = p.basis_combo.currentData() or "strand"
        s.concentration_source = p.conc_source_combo.currentData() or "absorbance"
        s.concentration_uM = p.conc_spin.value()
        s.concentration_in_cell = bool(p.conc_where_combo.currentData())
        self._update_enabled()
        self._show_formula()
        self._match_preset()
        self.app.recompute()
        if self.app.window.step_tabs.currentWidget() is p:
            sender_is_trim = p.begin_spin.hasFocus() or p.end_spin.hasFocus()
            self.app.window.show_plot("trim" if sender_is_trim else "converted")

    def reset(self):
        chosen = self.session.settings.chosen_columns
        self._seq_timer.stop()
        self.session.settings = ProcessingSettings(chosen_columns=chosen)
        self.load_settings()
        self.app.recompute()
        self.app.status("Processing settings reset to the values of the original analysis.")

    def update_view(self):
        s = self.session
        p = self.panel
        r = s.result
        if r is not None:
            p.factor_label.setText(f"factor = {r.factor:.6g}   (l_CD = {r.cd_pathlength_cm:g} cm)")
            how = "entered" if s.settings.concentration_source == "entered" else "from the absorbance"
            p.conc_label.setText(f"Strand concentration ({how}): {r.c_unmixed_uM:.4g} µM before mixing → "
                                 f"{r.c_cell_uM:.4g} µM in the cell")
            if s.settings.cd_pathlength_cm is None:
                self._loading = True
                p.cd_path_spin.setValue(r.cd_pathlength_cm)
                self._loading = False
            n = len(r.mean_df)
            p.trim_label.setText(f"{n} points averaged → {len(r.kinetics_df)} kept "
                                 f"(t = {r.kinetics_df['Time'].iloc[0]:g} … {r.kinetics_df['Time'].iloc[-1]:g} s)")
            p.set_status("✔ Conversion done – the Δε kinetics are ready for fitting.", True)
        else:
            p.factor_label.setText("factor = –")
            p.conc_label.setText("")
            p.trim_label.setText("")
            p.set_status(f"✘ {s.processing_error}" if s.processing_error else "", False)
        w = self.app.window
        mean_df = None
        if r is not None:
            mean_df = r.mean_df
        elif s.files and s.settings.chosen_columns:
            try:
                from src.modules.analysis.processing import average_traces
                mean_df = average_traces(s.files, s.settings.chosen_columns)
            except Exception:              # noqa: BLE001 - the error is shown in the status
                mean_df = None
        figures.average(w.plots["average"].figure, s.files, s.settings.chosen_columns, mean_df)
        w.plots["average"].redraw()
        figures.trimming(w.plots["trim"].figure, mean_df, s.settings.points_from_beginning,
                         s.settings.points_from_end)
        w.plots["trim"].redraw()
        figures.converted(w.plots["converted"].figure, r.kinetics_df if r is not None else None,
                          ylabel=r.y_label if r is not None else figures.DELTA_EPS)
        w.plots["converted"].redraw()
