# src/modules/data_io/prodata_binary.py
"""Reader of the binary Pro-Data files of the Applied Photophysics Chirascan
(*.dsx, "ProBinaryX"), the instrument's own format next to the CSV export.

Layout (little-endian), as found in Chirascan v4.4 files and checked against
their CSV exports (tests/test_prodata_binary.py, tools/check_dsx_against_csv.py):

    "ProBinaryX\\n", title, GUID, ...           fixed header (skipped)
    int32 n, n x "#remark\\0"                    #Date, #Temperature, #Pathlength, ...
    int32 n, n x "option\\0"                     e.g. Misc_AutoShutter:1
    int32 n, n x "Property -options\\0"          CircularDichroism, HV, Absorbance, ...
    int32 n_dims, then per dimension:
        "Name -options\\0", int32 count, count x float32   Time / Wavelength / Repeat axis
    int32 n_bytes, n_bytes/4 x float32           all values: property by property; within a
                                                 property the first dimension varies fastest
    history ...                                  (ignored)

The reader is pure Python + numpy and never executes anything from the file."""

import os
import struct
from dataclasses import dataclass, field

import numpy as np

MAGIC = b"ProBinaryX"


class ProDataBinaryError(RuntimeError):
    pass


@dataclass
class ProDataBinary:
    path: str
    remarks: list
    properties: list                 # names, e.g. ["CircularDichroism", "HV", ...]
    dimensions: list                 # [(name, options, np.ndarray axis)]
    data: dict = field(repr=False)   # property -> ndarray shaped like the dimensions (reversed order)
    raw: bytes = field(default=b"", repr=False)   # the file content

    def dimension(self, name):
        for n, _, axis in self.dimensions:
            if n.lower() == name.lower():
                return axis
        return None

    @property
    def kind(self):
        """'kinetics' (a time axis), 'spectrum' (a wavelength axis) or 'other'."""
        t = self.dimension("Time")
        w = self.dimension("Wavelength")
        if t is not None and len(t) > 1:
            return "kinetics"
        if w is not None and len(w) > 1:
            return "spectrum"
        return "other"


def _to_float64(values):
    """float32 -> float64 through the shortest decimal text of each value, so 0.1 stays 0.1
    (as in the CSV export) instead of 0.10000000149."""
    return np.asarray(values.astype(str), dtype=float)


def _cstring(raw, pos):
    end = raw.index(b"\x00", pos)
    return raw[pos:end].decode("latin-1"), end + 1


def _int32(raw, pos):
    return struct.unpack_from("<i", raw, pos)[0], pos + 4


def _string_list(raw, pos, max_count=1000):
    n, pos = _int32(raw, pos)
    if not 0 <= n <= max_count:
        raise ProDataBinaryError(f"unexpected list length {n}")
    items = []
    for _ in range(n):
        s, pos = _cstring(raw, pos)
        items.append(s)
    return items, pos


def _find_remarks(raw):
    """Position of the remark list: an int32 count followed by that many '#...' strings."""
    pos = raw.find(b"#", len(MAGIC))
    while pos != -1:
        if pos >= 4:
            n = struct.unpack_from("<i", raw, pos - 4)[0]
            if 1 <= n <= 200:
                try:
                    items, _ = _string_list(raw, pos - 4)
                    if all(s.startswith("#") for s in items):
                        return pos - 4
                except (ValueError, struct.error, ProDataBinaryError):
                    pass
        pos = raw.find(b"#", pos + 1)
    raise ProDataBinaryError("no remark block (#Date, #Pathlength, ...) found")


def read_prodata_binary(path, raw=None):
    """Read a .dsx file -> ProDataBinary. With `raw` (bytes) the content is taken from it
    (a copy stored in a project) and `path` is only its name."""
    if raw is None:
        with open(path, "rb") as f:
            raw = f.read()
    if not raw.startswith(MAGIC):
        raise ProDataBinaryError(f"{os.path.basename(path)} is not a readable Chirascan binary file "
                                 f"(it does not start with 'ProBinaryX' - the file is damaged or of "
                                 f"another kind)")
    try:
        pos = _find_remarks(raw)
        remarks, pos = _string_list(raw, pos)
        _options, pos = _string_list(raw, pos)
        props_full, pos = _string_list(raw, pos)
        n_dims, pos = _int32(raw, pos)
        if not 1 <= n_dims <= 10:
            raise ProDataBinaryError(f"unexpected number of dimensions {n_dims}")
        dims = []
        for _ in range(n_dims):
            desc, pos = _cstring(raw, pos)
            count, pos = _int32(raw, pos)
            if not 0 < count <= 50_000_000:
                raise ProDataBinaryError(f"unexpected axis length {count}")
            axis = _to_float64(np.frombuffer(raw, "<f4", count, pos))
            pos += 4 * count
            name, _, opts = desc.partition(" ")
            dims.append((name, opts.strip(), axis))
        n_bytes, pos = _int32(raw, pos)
        props = [p.split(" ")[0] for p in props_full]
        shape = [len(a) for _, _, a in dims]
        per_prop = int(np.prod(shape))
        if n_bytes != 4 * per_prop * len(props) or pos + n_bytes > len(raw):
            raise ProDataBinaryError(f"data block of {n_bytes} bytes does not match "
                                     f"{len(props)} properties x {shape}")
        values = _to_float64(np.frombuffer(raw, "<f4", per_prop * len(props), pos))
    except (ValueError, struct.error, IndexError) as exc:
        raise ProDataBinaryError(f"{os.path.basename(path)}: unreadable Pro-Data binary file ({exc})") from exc
    data = {}
    for k, p in enumerate(props):
        block = values[k * per_prop:(k + 1) * per_prop]
        data[p] = block.reshape(shape[::-1])          # the first dimension varies fastest
    return ProDataBinary(path=path, remarks=remarks, properties=props, dimensions=dims, data=data, raw=raw)


def remark_value(remarks, key):
    """'#Pathlength: 10' -> '10' for key 'Pathlength'."""
    for r in remarks:
        if r.startswith(f"#{key}:"):
            return r.split(":", 1)[1].strip()
    return None


def bandwidth_nm(dimensions):
    """Bandwidth from the wavelength options '-en 3.000000 -ex 3.000000' (entrance/exit slit, nm)."""
    for name, opts, _ in dimensions:
        if name.lower() == "wavelength":
            parts = opts.split()
            if "-en" in parts:
                try:
                    return f"{float(parts[parts.index('-en') + 1]):g}"
                except (IndexError, ValueError):
                    return None
    return None


def property_matrix(pb, prop):
    """(x axis, 2-D array [repeat or 1, point]) of a property along its time or wavelength axis."""
    arr = pb.data[prop]
    names = [n.lower() for n, _, _ in pb.dimensions]
    x_name = "time" if pb.kind == "kinetics" else "wavelength"
    x = pb.dimension(x_name)
    # move the x axis to the last position (it is the fastest = last of the reversed shape when first)
    axes_rev = names[::-1]
    arr = np.moveaxis(arr, axes_rev.index(x_name), -1)
    return x, arr.reshape(-1, arr.shape[-1])
