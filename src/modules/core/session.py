# src/modules/core/session.py
"""The state of one analysis (the "model" of MVC): loaded files, the
processing settings and result, the model specifications (editable p0 and
bounds), the stored fits and F-tests. Plain Python - the controllers change
it and tell the views."""

import gzip
import json
import os

import numpy as np

from src.modules.analysis import fitting, processing
from src.modules.analysis.models import MODEL_NAMES, default_f_tests, default_specs
from src.modules.data_io.loader import group_twins, read_data_file, twin_key
from src.version import APP_NAME, APP_VERSION

PROJECT_EXTENSION = ".sfkx"
PROJECT_FORMAT = 4          # 1: settings; 2: + fits, F-tests, report; 3: + CSV copies, window state, gzip;
                            # 4: + spectra, .dsx files


def _encode(obj):
    """Fit / F-test results -> JSON-compatible (numpy arrays tagged, so they come back as arrays)."""
    if isinstance(obj, np.ndarray):
        return {"__ndarray__": obj.tolist()}
    if isinstance(obj, dict):
        return {str(k): _encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_encode(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def _decode(obj):
    if isinstance(obj, dict):
        if set(obj) == {"__ndarray__"}:
            return np.asarray(obj["__ndarray__"], dtype=float)
        return {k: _decode(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode(v) for v in obj]
    return obj


class AnalysisSession:
    def __init__(self):
        self.files = []                    # kinetics (KineticsFile)
        self.spectra = []                  # spectra for display (Spectrum)
        self.last_added = {"kinetics": 0, "spectra": 0}
        self.settings = processing.ProcessingSettings()
        self.result = None                 # ProcessingResult or None
        self.processing_error = None       # text of the last processing error
        self.specs = default_specs()
        self.f_test_defs = default_f_tests()
        self.fits = {}                     # model name -> fit result
        self.f_tests = {}                  # comparison name -> F-test result
        self.check_starts = fitting.DEFAULT_CHECK_STARTS
        self.savgol_window = fitting.DEFAULT_SAVGOL_WINDOW
        self.project_path = None
        self.report_text = ""              # text of the Report tab (saved with the project)
        self.view_state = {}               # state of the window (selected model, plot options, ...)
        self.load_notes = []               # remarks of the last load (copies of files used, ...)
        self.saved_signature = self.signature()

    # ------------------------------------------------------------ files
    def add_files(self, paths):
        """Read data files (.csv / .dsx; kinetics and spectra are told apart by their content).
        A measurement present as both .csv and .dsx is loaded once. Returns (number added,
        [error texts]); self.last_added tells how many kinetics and spectra."""
        known = {twin_key(f.path) for f in self.files} | {twin_key(sp.path) for sp in self.spectra}
        added, errors = 0, []
        self.last_added = {"kinetics": 0, "spectra": 0}
        for group in group_twins(paths):
            if twin_key(group[0]) in known:
                continue
            group_errors = []
            for p in group:
                try:
                    kind, obj = read_data_file(p)
                except Exception as exc:      # noqa: BLE001 - every reading error is reported
                    group_errors.append(str(exc))
                    continue
                if kind == "spectrum":
                    self.spectra.append(obj)
                    self.last_added["spectra"] += 1
                else:
                    first = len(self.files)
                    self.files.append(obj)
                    self.last_added["kinetics"] += 1
                    # by default every trace of a newly added file is selected
                    self.settings.chosen_columns += [(first, c) for c in obj.traces]
                known.add(twin_key(p))
                added += 1
                group_errors = []             # the twin was read: its failure does not matter
                break
            errors += group_errors
        return added, errors

    def remove_spectrum(self, index):
        del self.spectra[index]

    def remove_file(self, index):
        del self.files[index]
        new = []
        for i, c in self.settings.chosen_columns:
            if i == index:
                continue
            new.append((i - 1 if i > index else i, c))
        self.settings.chosen_columns = new

    def clear(self):
        self.__init__()

    # ------------------------------------------------------------ processing
    def recompute(self):
        """Sections 2-3; keeps the error text instead of raising."""
        self.result = None
        self.processing_error = None
        if not self.files:
            self.processing_error = "No data loaded."
            return None
        try:
            self.result = processing.run_processing(self.files, self.settings)
        except processing.ProcessingError as exc:
            self.processing_error = str(exc)
        return self.result

    @property
    def fingerprint(self):
        return self.result.fingerprint if self.result is not None else None

    def current_fits(self):
        """Fits made on the current data (others are outdated)."""
        fp = self.fingerprint
        return {k: v for k, v in self.fits.items() if v["data_fingerprint"] == fp}

    def current_f_tests(self):
        fp = self.fingerprint
        return {k: v for k, v in self.f_tests.items() if v["data_fingerprint"] == fp}

    def is_current(self, fit):
        return fit is not None and fit["data_fingerprint"] == self.fingerprint

    # ------------------------------------------------------------ project file
    def to_dict(self):
        def clean(values):
            return [None if (isinstance(v, float) and not np.isfinite(v)) else v for v in values]

        return {
            "program": APP_NAME, "version": APP_VERSION,
            "files": [f.path for f in self.files],
            "spectra": [{"path": sp.path, "visible": sp.visible} for sp in self.spectra],
            "settings": self.settings.to_dict(),
            "check_starts": self.check_starts,
            "savgol_window": self.savgol_window,
            "models": {name: {"p0": list(map(float, s["p0"])),
                              "lower": clean(list(map(float, s["lower"]))),
                              "upper": clean(list(map(float, s["upper"]))),
                              "fixed": [bool(f) for f in s.get("fixed", [False] * len(s["p0"]))]}
                       for name, s in self.specs.items()},
            "f_tests": {name: {"p0_simple": list(map(float, d["p0_simple"])),
                               "p0_complex": list(map(float, d["p0_complex"]))}
                        for name, d in self.f_test_defs.items()},
        }

    def signature(self):
        """A short text that changes whenever something worth saving changes (unsaved-changes check)."""
        try:
            d = self.to_dict()
        except AttributeError:            # during __init__
            return ""
        d["file_sha1"] = [f.sha1 for f in self.files] + [sp.sha1 for sp in self.spectra]
        d["fit_results"] = sorted((k, v.get("data_fingerprint"), float(v["ss_res"])) for k, v in self.fits.items())
        d["f_test_results"] = sorted((k, v.get("data_fingerprint"), float(v["F_stat"])) for k, v in self.f_tests.items())
        return json.dumps(d, sort_keys=True, default=str)

    @property
    def has_unsaved_changes(self):
        if not self.files and not self.fits and not self.spectra:
            return False
        return self.signature() != self.saved_signature

    # ------------------------------------------------------------ whole state <-> file
    def build_state(self, report_text=None, view_state=None):
        """Everything of the analysis as a JSON-compatible dict (project file and automatic save):
        settings, model p0/bounds, F-test p0, fit options, a copy of every CSV file, all fits,
        F-tests, the report and the state of the window (view_state)."""
        if report_text is not None:
            self.report_text = report_text
        if view_state is not None:
            self.view_state = view_state
        d = self.to_dict()
        d["format"] = PROJECT_FORMAT
        d["embedded_files"] = [{"path": f.path, "name": f.name, "sha1": f.sha1, "content": f.raw_text,
                                "format": f.fmt} for f in self.files]
        d["embedded_spectra"] = [{"path": sp.path, "name": sp.name, "sha1": sp.sha1, "content": sp.content,
                                  "format": sp.fmt} for sp in self.spectra]
        d["fit_results"] = {k: _encode(v) for k, v in self.fits.items()}
        d["f_test_results"] = {k: _encode(v) for k, v in self.f_tests.items()}
        d["report"] = self.report_text
        d["view"] = _encode(self.view_state)
        return d

    def save_project(self, path, report_text=None, view_state=None):
        write_state_file(path, self.build_state(report_text, view_state))
        self.project_path = path
        self.saved_signature = self.signature()

    def load_project(self, path):
        """Open a project; returns [texts of the problems met]."""
        d = read_state_file(path)
        errors = self.load_state(d, os.path.dirname(os.path.abspath(path)))
        self.project_path = path
        self.saved_signature = self.signature()
        return errors

    def load_state(self, d, base_dir=None):
        """Restore from build_state(). The CSV files are read from their place when they are
        unchanged; otherwise (moved, deleted, edited) the copy stored in the project is used."""
        self.clear()
        errors, notes = [], []
        embedded = {e["path"]: e for e in d.get("embedded_files", [])}
        index_map = {}                                # old file index -> new (spectra leave the list)
        for old, p in enumerate(d.get("files", [])):
            kind, obj = self._restore_file(p, embedded.get(p), base_dir, errors, notes)
            if kind == "kinetics":
                index_map[old] = len(self.files)
                self.files.append(obj)
            elif kind == "spectrum":                  # saved by an older version as kinetics
                self.spectra.append(obj)
                notes.append(f"{obj.name} is a spectrum - it is now shown in the plot 'Spectra' and is no "
                             f"longer used as kinetics.")
        embedded_sp = {e["path"]: e for e in d.get("embedded_spectra", [])}
        for entry in d.get("spectra", []):
            p = entry.get("path")
            kind, obj = self._restore_file(p, embedded_sp.get(p), base_dir, errors, notes)
            if kind == "spectrum":
                obj.visible = bool(entry.get("visible", True))
                self.spectra.append(obj)
            elif kind == "kinetics":
                errors.append(f"{os.path.basename(p)} is no longer a spectrum - it was not loaded.")
        self.settings = processing.ProcessingSettings.from_dict(d.get("settings", {}))
        self.settings.chosen_columns = [(index_map[i], c) for i, c in self.settings.chosen_columns
                                        if i in index_map and c in self.files[index_map[i]].traces]
        self.check_starts = int(d.get("check_starts", self.check_starts))
        self.savgol_window = int(d.get("savgol_window", self.savgol_window))

        def restore(values, inf):
            return [inf if v is None else float(v) for v in values]

        for name, m in d.get("models", {}).items():
            if name in self.specs and len(m.get("p0", [])) == len(self.specs[name]["p0"]):
                self.specs[name]["p0"] = [float(v) for v in m["p0"]]
                self.specs[name]["lower"] = restore(m["lower"], -np.inf)
                self.specs[name]["upper"] = restore(m["upper"], np.inf)
                fixed = m.get("fixed")
                if isinstance(fixed, list) and len(fixed) == len(self.specs[name]["p0"]):
                    self.specs[name]["fixed"] = [bool(f) for f in fixed]
        for name, t in d.get("f_tests", {}).items():
            if name in self.f_test_defs:
                self.f_test_defs[name].update({k: [float(v) for v in t[k]] for k in ("p0_simple", "p0_complex")
                                               if k in t})
        self.recompute()
        # results: kept as they were; fits made on other data are marked outdated by their fingerprint
        for name, fit in d.get("fit_results", {}).items():
            try:
                fit = _decode(fit)
                if fit.get("model") in self.specs:
                    self.fits[name] = fit
            except (TypeError, ValueError):
                errors.append(f"The stored fit {name!r} could not be read.")
        for name, t in d.get("f_test_results", {}).items():
            try:
                self.f_tests[name] = _decode(t)
            except (TypeError, ValueError):
                errors.append(f"The stored F-test {name!r} could not be read.")
        self.report_text = d.get("report", "")
        self.view_state = _decode(d.get("view", {})) or {}
        self.load_notes = notes
        return errors


    @staticmethod
    def _restore_file(p, copy, base_dir, errors, notes):
        """A data file of a project: read from its place when unchanged; otherwise (moved, deleted,
        edited) the copy stored in the project. -> (kind, object) or (None, None)."""
        candidates = [p]
        if base_dir:                                  # project moved together with its data
            candidates.append(os.path.join(base_dir, os.path.basename(p)))
        result = (None, None)
        for c in candidates:
            if not os.path.isfile(c):
                continue
            try:
                result = read_data_file(c)
            except Exception as exc:                  # noqa: BLE001
                errors.append(str(exc))
                result = (None, None)
                continue
            sha1 = result[1].sha1
            if copy is not None and sha1 != copy["sha1"]:
                notes.append(f"{os.path.basename(c)} was changed since the project was saved - the "
                             f"copy stored in the project is used.")
                result = (None, None)
            break
        if result[0] is None and copy is not None:
            try:
                result = read_data_file(p, content=copy["content"], fmt=copy.get("format", "csv"))
                if not any(os.path.isfile(c) for c in candidates):
                    notes.append(f"{os.path.basename(p)} not found - the copy stored in the project is used.")
            except Exception as exc:                  # noqa: BLE001
                errors.append(str(exc))
        if result[0] is None and copy is None:
            errors.append(f"Data file not found: {p}")
        return result


def write_state_file(path, state):
    """gzip-compressed JSON, written atomically (a temporary file renamed over the target, so an
    interrupted save never leaves a broken file)."""
    data = gzip.compress(json.dumps(state, ensure_ascii=False).encode("utf-8"), compresslevel=6)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_state_file(path):
    """A project / automatic save: gzip-compressed JSON (or plain JSON of the first version)."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


__all__ = ["AnalysisSession", "MODEL_NAMES", "PROJECT_EXTENSION"]
