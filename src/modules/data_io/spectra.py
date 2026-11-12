# src/modules/data_io/spectra.py
"""CD spectra measured next to the kinetics (wavelength scans of the sample,
the buffer "background", baselines): read from the Chirascan CSV export or the
binary .dsx file, for display only (they are not averaged or fitted).

Every property of the file is kept (CircularDichroism, HV, Absorbance, ...),
each as a 2-D array [scan, wavelength] - usually a single scan."""

import base64
import hashlib
import os
from dataclasses import dataclass, field

import numpy as np

from src.modules.data_io.chirascan_reader import ChirascanFormatError, _read_text, read_metadata

# axis label of each property
PROPERTY_LABELS = {"CircularDichroism": "CD (mdeg)", "HV": "HV (V)", "Absorbance": "Absorbance",
                   "Voltage": "Voltage (V)", "Count": "Count", "Temperature": "Temperature (°C)",
                   "SE": "Standard error of CD (mdeg)"}
PROPERTY_NAMES = {"CircularDichroism": "Circular dichroism", "HV": "HV (detector voltage)",
                  "Absorbance": "Absorbance", "Voltage": "Voltage", "Count": "Count",
                  "Temperature": "Temperature", "SE": "Standard error (SE)"}


@dataclass
class Spectrum:
    path: str
    metadata: dict
    wavelength: np.ndarray = field(repr=False)
    values: dict = field(repr=False)            # property -> ndarray [scan, wavelength]
    content: str = field(default="", repr=False)   # the file (text; base64 for .dsx) - stored in projects
    fmt: str = "csv"
    visible: bool = True

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def stem(self):
        return os.path.splitext(self.name)[0]

    @property
    def sha1(self):
        return hashlib.sha1(self.content.encode("utf-8")).hexdigest()

    @property
    def properties(self):
        return list(self.values)

    @property
    def n_scans(self):
        return next(iter(self.values.values())).shape[0] if self.values else 0

    def curve(self, prop="CircularDichroism", hv_max=None):
        """(wavelength ascending, mean over the scans) of a property, or None if it is missing.
        With hv_max the points where the detector voltage HV exceeds it are NaN (not drawn)."""
        m = self.values.get(prop)
        if m is None:
            return None
        y = np.nanmean(m, axis=0) if m.shape[0] > 1 else m[0].copy()
        if hv_max is not None and prop != "HV":
            y = np.where(self.hv_mask(hv_max), np.nan, y)
        order = np.argsort(self.wavelength)
        return self.wavelength[order], y[order]

    def hv_mask(self, hv_max):
        """True where HV > hv_max (in the order of the file); all False without an HV record."""
        hv = self.values.get("HV")
        if hv is None or hv_max is None:
            return np.zeros(len(self.wavelength), dtype=bool)
        return np.nanmax(hv, axis=0) > hv_max

    @property
    def range_text(self):
        w = self.wavelength
        return f"{np.min(w):g}–{np.max(w):g}" if len(w) else ""


def subtract(curve, baseline):
    """curve - baseline, the baseline interpolated onto the wavelengths of the curve
    (NaN outside the baseline's range)."""
    x, y = curve
    bx, by = baseline
    b = np.interp(x, bx, by, left=np.nan, right=np.nan)
    return x, y - b


# ------------------------------------------------------------------ CSV
def _csv_blocks(text):
    """The data blocks of a ProDataCSV spectrum: {property: (x, 2-D [point, scan])}."""
    lines = text.splitlines()
    try:
        i = next(k for k, ln in enumerate(lines) if ln.strip() == "Data:")
    except StopIteration:
        raise ChirascanFormatError("no 'Data:' block was found") from None
    out, j = {}, i + 1
    while j < len(lines) and not lines[j].startswith("History"):
        if not lines[j].strip():
            j += 1
            continue
        header = []
        while j < len(lines) and lines[j].strip() and not _is_number(lines[j].split(",")[0]):
            header.append(lines[j])
            j += 1
        rows = []
        while j < len(lines) and lines[j].strip() and _is_number(lines[j].split(",")[0]):
            rows.append([float(v) if v.strip() else np.nan for v in lines[j].rstrip(",").split(",")])
            j += 1
        names = [h.split(",")[0].strip() for h in header]
        names = [n for n in names if n and n not in ("Wavelength", "Wavelength:", "Time", "Repeat", "Temperature:")]
        if names and rows:
            width = max(len(r) for r in rows)
            arr = np.array([r + [np.nan] * (width - len(r)) for r in rows])
            out.setdefault(names[0], (arr[:, 0], arr[:, 1:]))
        if not header and not rows:
            j += 1
    return out


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_spectrum_csv(path, text=None):
    try:
        if text is None:
            text = _read_text(path)
        blocks = _csv_blocks(text)
        if not blocks:
            raise ChirascanFormatError("no spectrum data was found")
        x = next(iter(blocks.values()))[0]
        values = {p: m.T for p, (bx, m) in blocks.items() if len(bx) == len(x)}
        md = read_metadata(text.splitlines(keepends=True), path)
        for line in text.splitlines():           # "Wavelength,Wavelength: 210nm - 330nm, Step Size: 0.5nm,Bandwidth: 3nm"
            if line.startswith("Wavelength,") and "Bandwidth" in line:
                md["Bandwidth (nm)"] = line.split("Bandwidth:")[1].replace("nm", "").split(",")[0].strip()
                break
    except ChirascanFormatError as exc:
        raise ChirascanFormatError(f"Failed to read the spectrum {os.path.basename(path)!r}: {exc}") from exc
    except (OSError, ValueError, IndexError) as exc:
        raise ChirascanFormatError(f"Failed to read the spectrum {os.path.basename(path)!r}: {exc}") from exc
    sp = Spectrum(path=path, metadata=md, wavelength=x, values=values, content=text, fmt="csv")
    sp.metadata["Wavelength (nm)"] = sp.range_text
    return sp


# ------------------------------------------------------------------ binary .dsx
def spectrum_from_binary(pb, path=None):
    from src.modules.data_io.prodata_binary import bandwidth_nm, property_matrix, remark_value
    path = path or pb.path
    if pb.kind != "spectrum":
        raise ChirascanFormatError(f"{os.path.basename(path)!r} is not a spectrum")
    values = {}
    x = None
    for p in pb.properties:
        x, m = property_matrix(pb, p)
        values[p] = m
    md = {"File": path, "Measurement date": remark_value(pb.remarks, "Date"),
          "Temperature": remark_value(pb.remarks, "Temperature"),
          "Pathlength (mm)": remark_value(pb.remarks, "Pathlength"),
          "Wavelength (nm)": None, "Bandwidth (nm)": bandwidth_nm(pb.dimensions)}
    sp = Spectrum(path=path, metadata=md, wavelength=x, values=values,
                  content=base64.b64encode(pb.raw).decode("ascii"), fmt="dsx")
    sp.metadata["Wavelength (nm)"] = sp.range_text
    return sp


def read_spectrum(path, content=None, fmt=None):
    """A spectrum from a .csv or .dsx file (or from the copy `content` stored in a project)."""
    from src.modules.data_io.prodata_binary import ProDataBinaryError, read_prodata_binary
    fmt = fmt or ("dsx" if path.lower().endswith(".dsx") else "csv")
    if fmt == "csv":
        return read_spectrum_csv(path, text=content)
    try:
        raw = base64.b64decode(content) if content is not None else None
        return spectrum_from_binary(read_prodata_binary(path, raw=raw), path)
    except (OSError, ValueError, ProDataBinaryError) as exc:
        raise ChirascanFormatError(f"Failed to read {os.path.basename(path)!r}: {exc}") from exc
