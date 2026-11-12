# src/modules/data_io/loader.py
"""One entry point for every data file: a Chirascan CSV export or binary .dsx
file is read and recognised as kinetics or a spectrum.

The Chirascan software writes a measurement as "name00000.dsx" and its export
as "name00000.csv". When both are present only one is loaded: the CSV (as in
earlier versions, so existing projects keep their files), or the .dsx when the
CSV cannot be read."""

import base64
import os

from src.modules.data_io.chirascan_reader import (ChirascanFormatError, _read_text, csv_kind, kinetics_from_binary,
                                                  read_chirascan_csv)
from src.modules.data_io.prodata_binary import ProDataBinaryError, read_prodata_binary
from src.modules.data_io.spectra import read_spectrum_csv, spectrum_from_binary


def file_format(path):
    return "dsx" if os.path.splitext(path)[1].lower() == ".dsx" else "csv"


def read_data_file(path, content=None, fmt=None):
    """-> ("kinetics", KineticsFile) or ("spectrum", Spectrum). `content`: the copy stored in a
    project (text; base64 for .dsx). Raises ChirascanFormatError."""
    fmt = fmt or file_format(path)
    name = os.path.basename(path)
    if fmt == "dsx":
        try:
            raw = base64.b64decode(content) if content is not None else None
            pb = read_prodata_binary(path, raw=raw)
        except (OSError, ValueError, ProDataBinaryError) as exc:
            raise ChirascanFormatError(f"Failed to read {name!r}: {exc}") from exc
        if pb.kind == "kinetics":
            return "kinetics", kinetics_from_binary(pb, path)
        if pb.kind == "spectrum":
            return "spectrum", spectrum_from_binary(pb, path)
        dims = ", ".join(f"{n} {len(a)}" for n, _, a in pb.dimensions)
        raise ChirascanFormatError(f"{name!r} is neither kinetics nor a spectrum ({dims})")
    try:
        text = content if content is not None else _read_text(path)
    except OSError as exc:
        raise ChirascanFormatError(f"Failed to read {name!r}: {exc}") from exc
    if csv_kind(text) == "spectrum":
        return "spectrum", read_spectrum_csv(path, text=text)
    return "kinetics", read_chirascan_csv(path, text=text)


def twin_key(path):
    """Files of one measurement (.csv export + .dsx) share this key."""
    return os.path.normcase(os.path.splitext(os.path.abspath(path))[0])


def group_twins(paths):
    """[[path, twin...]] in the order of first appearance; in each group the CSV comes first."""
    groups, order = {}, []
    for p in paths:
        k = twin_key(p)
        if k not in groups:
            groups[k] = []
            order.append(k)
        if p not in groups[k]:
            groups[k].append(p)
    return [sorted(groups[k], key=lambda p: file_format(p) != "csv") for k in order]
