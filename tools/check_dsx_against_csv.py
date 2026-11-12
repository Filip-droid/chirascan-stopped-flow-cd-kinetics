"""Checks the reader of the binary Pro-Data files (*.dsx) against their CSV
exports: every property, every repeat, the axis. Usage:

    python tools/check_dsx_against_csv.py <folder with .dsx and .csv files> ...

Prints one line per file pair and a summary; exit code 1 if any differs."""

import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.modules.data_io.prodata_binary import property_matrix, read_prodata_binary  # noqa: E402


def csv_blocks(path):
    """ProDataCSV -> {property: 2-D array [point, x + values]}."""
    with open(path, encoding="latin-1") as f:
        lines = f.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = lines.index("Data:")
    out, j = {}, i + 1
    while j < len(lines) and not lines[j].startswith("History"):
        if not lines[j].strip():
            j += 1
            continue
        hdr = []
        while j < len(lines) and not (lines[j][:1].isdigit() or lines[j][:1] == "-"):
            hdr.append(lines[j])
            j += 1
        rows = []
        while j < len(lines) and lines[j].strip():
            rows.append([float(v) for v in lines[j].rstrip(",").split(",") if v != ""])
            j += 1
        names = [h.split(",")[0] for h in hdr if h and h.split(",")[0] not in ("Wavelength", "Time", "Wavelength:")]
        if names and rows:
            out[names[0]] = np.array(rows)
    return out


def check(dsx):
    csv = os.path.splitext(dsx)[0] + ".csv"
    if not os.path.isfile(csv):
        return None, "no CSV twin"
    pb = read_prodata_binary(dsx)
    ref = csv_blocks(csv)
    for p in pb.properties:
        x, m = property_matrix(pb, p)
        r = ref.get(p)
        if r is None:
            return False, f"{p} missing in the CSV"
        if r.shape[0] != len(x) or not np.allclose(r[:, 0], x, rtol=1e-5):
            return False, f"{p}: axis differs"
        if r[:, 1:].T.shape != m.shape or not np.allclose(r[:, 1:].T, m, rtol=1e-4, atol=1e-5):
            return False, f"{p}: values differ"
    dims = ", ".join(f"{n} {len(a)}" for n, _, a in pb.dimensions)
    return True, f"{pb.kind}: {dims}"


def main(folders):
    n_ok = n_bad = n_skip = 0
    for folder in folders:
        for dsx in sorted(glob.glob(os.path.join(folder, "**", "*.dsx"), recursive=True)):
            try:
                ok, note = check(dsx)
            except Exception as exc:              # noqa: BLE001
                ok, note = False, f"error: {exc}"
            tag = {True: "OK  ", False: "BAD ", None: "skip"}[ok]
            n_ok += ok is True
            n_bad += ok is False
            n_skip += ok is None
            print(f"{tag} {os.path.relpath(dsx, folder)}  ({note})")
    print(f"\n{n_ok} identical, {n_bad} different, {n_skip} without CSV")
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["."]))
