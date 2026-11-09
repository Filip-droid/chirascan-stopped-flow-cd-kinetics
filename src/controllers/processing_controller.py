# src/controllers/processing_controller.py
"""Step 2 - trimming, sample and conversion settings."""

from src.modules.analysis.processing import SEQUENCE_PRESETS, ProcessingSettings
from src.modules.visualization import figures


class ProcessingController:
    def __init__(self, app):
        self.app = app
        self.session = app.session
        self.panel = p = app.window.processing_panel
        self._loading = False
        self.load_settings()
        for w in (p.begin_spin, p.end_spin, p.length_spin):
            w.valueChanged.connect(self._changed)
        for w in (p.eps_spin, p.absorbance_spin, p.abs_path_spin, p.cd_path_spin, p.baseline_spin):
            w.valueChanged.connect(self._changed)
        p.cd_path_header_check.toggled.connect(self._changed)
        p.preset_combo.currentIndexChanged.connect(self._preset)
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
        self._match_preset()
        self._loading = False

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
        self._match_preset()
        self.app.recompute()
        if self.app.window.step_tabs.currentWidget() is p:
            sender_is_trim = p.begin_spin.hasFocus() or p.end_spin.hasFocus()
            self.app.window.show_plot("trim" if sender_is_trim else "converted")

    def reset(self):
        chosen = self.session.settings.chosen_columns
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
        figures.converted(w.plots["converted"].figure, r.kinetics_df if r is not None else None)
        w.plots["converted"].redraw()
