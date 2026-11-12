# src/modules/data_io/chirascan_reader.py
"""Reading of Chirascan (Applied Photophysics) stopped-flow kinetics: the CSV
export and the instrument's binary file (*.dsx, see prodata_binary.py).

A port of section 1 of the notebook: the metadata header (date, temperature,
path length, wavelength, bandwidth) and the "Data:" block with the time column
and one column per repeat. Columns that are all NaN or all zero (unused
repeats) and the detector high-voltage column (HV) are dropped; the traces are
named "CD kinetics 1", "CD kinetics 2", ...

A CSV export of a spectrum (wavelength scan, "sp ...", baselines) is
recognised and refused here - spectra are read by spectra.py."""

import base64
import glob
import hashlib
import io
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

METADATA_COLUMNS = ["File", "Measurement date", "Temperature", "Pathlength (mm)",
                    "Wavelength (nm)", "Bandwidth (nm)"]


class ChirascanFormatError(RuntimeError):
    """The file is not a Chirascan CSV export this program can read."""


@dataclass
class KineticsFile:
    """One loaded CSV file: its path, header metadata and data (Time + traces)."""
    path: str
    metadata: dict
    data: pd.DataFrame = field(repr=False)
    raw_text: str = field(default="", repr=False)      # the file as read (stored in projects)
    fmt: str = "csv"                                    # "csv" or "dsx" (raw_text is then base64)

    @property
    def sha1(self):
        return hashlib.sha1(self.raw_text.encode("utf-8")).hexdigest()

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def traces(self):
        """Names of the kinetic traces (all columns except Time)."""
        return list(self.data.columns[1:])

    @property
    def pathlength_cm(self):
        """CD path length from the header (mm in the file) in cm, or None."""
        try:
            return float(self.metadata.get("Pathlength (mm)")) / 10.0
        except (TypeError, ValueError):
            return None


def _read_text(path):
    """The file as text (UTF-8, else Windows-1250, else Latin-1), with \\n line ends."""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "cp1250", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_metadata(lines, path):
    """Header metadata (pass 1 of the notebook)."""
    date = temperature = pathlength = wavelength = bandwidth = None
    for line in lines:
        if "#Date:" in line:
            date = line.split(":")[1].strip()
        elif "#Temperature:" in line:
            temperature = line.split(":")[1].strip()
        elif "#Pathlength:" in line:
            pathlength = line.split(":")[1].strip()
        if "Wavelength" in line and "Bandwidth" in line:
            for part in line.split(","):
                if "Wavelength:" in part:
                    wavelength = part.split(":")[1].replace("nm", "").strip()
                elif "Bandwidth" in part:
                    bandwidth = part.split(":")[1].replace("nm", "").strip()
            break
    return {"File": path, "Measurement date": date, "Temperature": temperature,
            "Pathlength (mm)": pathlength, "Wavelength (nm)": wavelength, "Bandwidth (nm)": bandwidth}


def csv_kind(text):
    """'kinetics', 'spectrum' or 'unknown' for a Chirascan ProDataCSV export, from the header
    of the first data block: kinetics have a time axis ("Time,Repeat" / "Time,"), spectra start
    with the wavelength axis ("Wavelength,")."""
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "Data:")
    except StopIteration:
        return "unknown"
    header = []
    for ln in lines[start + 1:start + 12]:
        first = ln.split(",")[0].strip()
        if not ln.strip():
            if header:
                break
            continue
        try:
            float(first)
            break
        except ValueError:
            header.append(first)
    if "Time" in header:
        return "kinetics"
    if header and header[0] in ("Wavelength", "Temperature"):
        return "spectrum"
    return "unknown"


def _data_block(lines):
    """(start_index, end_index) of the data block (pass 2 of the notebook).

    The block starts after the "Data:" keyword (first numeric line) and ends at
    the first empty line; this relies on the exported data containing no
    missing values."""
    start_index = None
    end_index = None
    for i, line in enumerate(lines):
        if "Data:" in line:
            start_index = i
        elif start_index is not None and "." in line:
            if end_index is None:
                start_index = i
            end_index = i - 1
        elif start_index is not None and end_index is not None and line.strip() == "":
            break
    if start_index is None or end_index is None:
        raise ChirascanFormatError("no 'Data:' block with numeric data was found")
    return start_index, end_index


def read_chirascan_csv(path, text=None):
    """Read one Chirascan CSV export -> KineticsFile. With `text` the content is
    taken from it (a copy stored in a project) and `path` is only its name."""
    try:
        if text is None:
            text = _read_text(path)
        if csv_kind(text) == "spectrum":
            raise ChirascanFormatError("it is a spectrum (wavelength scan), not a kinetic measurement")
        lines = text.splitlines(keepends=True)
        metadata = read_metadata(lines, path)
        start_index, end_index = _data_block(lines)
        df = pd.read_csv(io.StringIO(text), delimiter=",", skiprows=start_index - 1,
                         nrows=end_index - start_index + 2)
        df.rename(columns={"Unnamed: 0": "Time"}, inplace=True)
        df = df.dropna(axis=1, how="all")              # columns containing only NaN
        df = df.loc[:, (df != 0).any(axis=0)]          # columns containing only zeros (unused repeats)
        if "HV" in df.columns:                         # detector high-voltage column
            df = df.drop(columns="HV")
        if df.shape[1] < 2:
            raise ChirascanFormatError("the data block contains no kinetic trace")
        df.columns = ["Time"] + [f"CD kinetics {i + 1}" for i in range(df.shape[1] - 1)]
        df = df.apply(pd.to_numeric, errors="raise").reset_index(drop=True)
    except ChirascanFormatError as exc:
        raise ChirascanFormatError(
            f"Failed to read {os.path.basename(path)!r}: {exc}. Check that it is a Chirascan CSV "
            f"export (metadata header + 'Data:' block).") from exc
    except (OSError, ValueError, TypeError, IndexError, pd.errors.ParserError) as exc:
        raise ChirascanFormatError(
            f"Failed to read {os.path.basename(path)!r}. Check that it is a Chirascan CSV export "
            f"(metadata header + 'Data:' block). Original error: {exc}") from exc
    return KineticsFile(path=path, metadata=metadata, data=df, raw_text=text)


def kinetics_from_binary(pb, path=None):
    """KineticsFile from a read .dsx file (ProDataBinary of kind 'kinetics'): the circular
    dichroism of every repeat at the (single) wavelength, metadata from the remarks."""
    from src.modules.data_io.prodata_binary import bandwidth_nm, property_matrix, remark_value
    path = path or pb.path
    name = os.path.basename(path)
    if pb.kind != "kinetics":
        raise ChirascanFormatError(f"{name!r} is a spectrum (wavelength scan), not a kinetic measurement")
    prop = "CircularDichroism" if "CircularDichroism" in pb.properties else pb.properties[0]
    wl = pb.dimension("Wavelength")
    if wl is not None and len(wl) > 1:
        raise ChirascanFormatError(f"{name!r} holds kinetics at {len(wl)} wavelengths; only single-wavelength "
                                   f"kinetics can be analysed")
    t, m = property_matrix(pb, prop)                 # [repeat, time]
    df = pd.DataFrame({"Time": t})
    k = 0
    for row in m:
        if np.all(np.isnan(row)) or not np.any(row != 0):   # unused repeats (as in the CSV reader)
            continue
        k += 1
        df[f"CD kinetics {k}"] = row
    if k == 0:
        raise ChirascanFormatError(f"{name!r} contains no kinetic trace")
    metadata = {"File": path, "Measurement date": remark_value(pb.remarks, "Date"),
                "Temperature": remark_value(pb.remarks, "Temperature"),
                "Pathlength (mm)": remark_value(pb.remarks, "Pathlength"),
                "Wavelength (nm)": f"{wl[0]:g}" if wl is not None and len(wl) else None,
                "Bandwidth (nm)": bandwidth_nm(pb.dimensions)}
    return KineticsFile(path=path, metadata=metadata, data=df,
                        raw_text=base64.b64encode(pb.raw).decode("ascii"), fmt="dsx")


def read_kinetics_dsx(path, content=None):
    """Read kinetics from a binary .dsx file. `content`: the base64 text stored in a project."""
    from src.modules.data_io.prodata_binary import ProDataBinaryError, read_prodata_binary
    try:
        raw = base64.b64decode(content) if content is not None else None
        pb = read_prodata_binary(path, raw=raw)
    except (OSError, ValueError, ProDataBinaryError) as exc:
        raise ChirascanFormatError(f"Failed to read {os.path.basename(path)!r}: {exc}") from exc
    return kinetics_from_binary(pb, path)


DATA_EXTENSIONS = (".csv", ".dsx")


def data_files_in(directory):
    """All data files (CSV exports and binary .dsx files) of a folder, sorted by name."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Data directory not found: {directory!r}")
    files = sorted(f for f in glob.glob(os.path.join(directory, "*"))
                   if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS and os.path.isfile(f))
    if not files:
        raise FileNotFoundError(f"No CSV or DSX files found in {directory!r}.")
    return files


def csv_files_in(directory):
    """All CSV files of a folder, sorted by name."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Data directory not found: {directory!r}")
    files = sorted(glob.glob(os.path.join(directory, "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory!r}.")
    return files
