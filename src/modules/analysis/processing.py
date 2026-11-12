# src/modules/analysis/processing.py
"""Sections 2 and 3 of the notebook: averaging of the selected traces,
trimming of points at the beginning/end, baseline subtraction and conversion
of the CD signal from mdeg to molar circular dichroism (Δε, M⁻¹ cm⁻¹, per
strand):

    Δε = (θ[mdeg] − baseline) · (N · ε_nt · l_abs) / (32980 · 0.5 · A · l_CD)

- 32980 converts ellipticity in mdeg to differential absorbance.
- c follows from the absorbance A of the UNMIXED solution: A = N · ε_nt · c · l_abs.
- 0.5: the 1:1 mixing in the stopped-flow halves the concentration.
- l_abs, l_CD: optical path lengths of the absorbance and CD measurements.

Every step starts from the output of the previous one and never modifies its
input, so any step can be recomputed safely."""

import hashlib
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from src.modules.analysis.models import DELTA_EPS, DELTA_EPS_BASES, delta_eps_label

AVERAGE_COLUMN = "Average CD kinetics"
MDEG_TO_DELTA_A = 32980.0
MIXING_DILUTION = 0.5

# Sequence presets from the notebook: name -> (length in nt, ε per nucleotide)
SEQUENCE_PRESETS = {
    "TTT": (21, 10626),
    "TT2T": (22, 10530),
    "TT3T": (23, 10443),
    "TT4T": (24, 10363),
    "TT5T": (25, 10289),
    "T3T3T3": (27, 10158),
    "1/x TT3T": (23, 10431),
}


@dataclass
class ProcessingSettings:
    """All user inputs of sections 2 and 3."""
    chosen_columns: list = field(default_factory=list)   # [(file index, column name), ...]
    points_from_beginning: int = 1
    points_from_end: int = 0
    sequence: str = ""                                    # 5'->3'; when given, length and ε come from it
    sequence_length: int = 23
    extinction_coefficient: float = 10443.0
    absorbance: float = 1.6079
    baseline: float = 0.42
    absorbance_pathlength_cm: float = 1.0
    cd_pathlength_cm: object = None                       # None = read from the CSV header
    delta_eps_basis: str = "strand"                       # Δε per "strand" (whole sequence) or per "nucleotide"
    concentration_source: str = "absorbance"              # "absorbance" (A, N, ε) or "entered" (concentration_uM)
    concentration_uM: float = 10.0                        # strand concentration entered directly (µM)
    concentration_in_cell: bool = False                   # the entered value is after the 1:1 mixing (in the cell)

    def to_dict(self):
        d = asdict(self)
        d["chosen_columns"] = [list(c) for c in self.chosen_columns]
        return d

    @classmethod
    def from_dict(cls, d):
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                setattr(s, k, v)
        s.chosen_columns = [tuple(c) for c in s.chosen_columns]
        return s


class ProcessingError(ValueError):
    pass


def average_traces(files, chosen_columns):
    """mean_df: Time of the first selected trace + mean of the selected traces."""
    if not chosen_columns:
        raise ProcessingError("No kinetic trace is selected - tick at least one trace.")
    try:
        first_index, _ = chosen_columns[0]
        mean_df = pd.DataFrame()
        mean_df["Time"] = files[first_index].data["Time"]
        for index, column in chosen_columns:
            trace = files[index].data[column]
            if AVERAGE_COLUMN not in mean_df.columns:
                mean_df[AVERAGE_COLUMN] = trace
            else:
                mean_df[AVERAGE_COLUMN] += trace
        mean_df[AVERAGE_COLUMN] /= len(chosen_columns)
    except (IndexError, KeyError) as exc:
        raise ProcessingError(f"Invalid selected trace ({exc}).") from exc
    if mean_df[AVERAGE_COLUMN].isna().any():
        raise ProcessingError("The selected traces have different numbers of points; "
                              "select traces measured with the same time axis.")
    return mean_df


def trim(mean_df, from_beginning, from_end):
    """trimmed_df: points removed from the beginning (dead time) and the end."""
    if from_beginning < 0 or from_end < 0:
        raise ProcessingError("The number of points to remove must not be negative.")
    if from_beginning + from_end >= len(mean_df):
        raise ProcessingError("Too many points to remove - no data would be left.")
    return mean_df.iloc[from_beginning:len(mean_df) - from_end]


def cd_pathlength_used(files, settings):
    """CD path length (cm): the manual value, or the common value of the headers."""
    if settings.cd_pathlength_cm is not None:
        return float(settings.cd_pathlength_cm)
    try:
        values = {float(files[i].metadata["Pathlength (mm)"]) / 10 for i, _ in settings.chosen_columns}
    except (TypeError, ValueError) as exc:
        raise ProcessingError("The path length was not found in the CSV header - "
                              "enter the CD path length manually.") from exc
    if len(values) != 1:
        raise ProcessingError(f"The selected CSV files have different path lengths in the header "
                              f"({sorted(values)} cm). Select files measured with the same path length.")
    return values.pop()


def strand_concentrations(settings):
    """(before mixing, in the cell) strand concentration in M.

    From the absorbance: c = A / (N·ε·l_abs) of the unmixed solution; entered: the value given, before or
    after the 1:1 mixing. In the cell the concentration is half of the unmixed one (MIXING_DILUTION)."""
    if settings.concentration_source == "entered":
        c = float(settings.concentration_uM) * 1e-6
        if c <= 0:
            raise ProcessingError("The concentration must be greater than zero.")
        if settings.concentration_in_cell:
            return c / MIXING_DILUTION, c
        return c, c * MIXING_DILUTION
    strand_eps = settings.sequence_length * settings.extinction_coefficient
    if strand_eps <= 0 or settings.absorbance_pathlength_cm <= 0:
        raise ProcessingError("The sequence length, ε and the path length of the absorbance measurement "
                              "must be greater than zero.")
    if settings.absorbance <= 0:
        raise ProcessingError("The absorbance must be greater than zero.")
    c = settings.absorbance / (strand_eps * settings.absorbance_pathlength_cm)
    return c, c * MIXING_DILUTION


def conversion_factor(settings, cd_pathlength_cm):
    """mdeg -> Δε: factor = 1 / (32980 · c_cell · l_CD), c_cell the strand concentration in the cell.
    From the absorbance this is N·ε·l_abs / (32980 · 0.5 · A · l_CD), as in the original analysis.
    Per nucleotide: the concentration of nucleotides is N times larger, so Δε is N times smaller."""
    if cd_pathlength_cm is None or cd_pathlength_cm <= 0:
        raise ProcessingError("The CD path length must be greater than zero.")
    if settings.concentration_source == "absorbance":
        # the original expression (kept for identical rounding with the notebook)
        try:
            factor = ((settings.sequence_length * settings.extinction_coefficient * settings.absorbance_pathlength_cm)
                      / (MDEG_TO_DELTA_A * MIXING_DILUTION * settings.absorbance * cd_pathlength_cm))
        except ZeroDivisionError as exc:
            raise ProcessingError("The absorbance and the CD path length must be non-zero.") from exc
    else:
        _, c_cell = strand_concentrations(settings)
        factor = 1.0 / (MDEG_TO_DELTA_A * c_cell * cd_pathlength_cm)
    if settings.delta_eps_basis == "nucleotide":
        if settings.sequence_length <= 0:
            raise ProcessingError("Δε per nucleotide needs the sequence length.")
        factor /= settings.sequence_length
    return factor


def convert(trimmed_df, baseline, factor):
    """kinetics_df: (signal − baseline) · factor."""
    kinetics_df = trimmed_df.copy()
    kinetics_df[AVERAGE_COLUMN] = (trimmed_df[AVERAGE_COLUMN] - baseline) * factor
    return kinetics_df


def data_fingerprint(df):
    """Short hash of the analysed data; detects fits that do not belong to the current data."""
    arr = np.ascontiguousarray(df[["Time", AVERAGE_COLUMN]].to_numpy(dtype=float))
    return hashlib.sha256(arr.tobytes()).hexdigest()[:16]


@dataclass
class ProcessingResult:
    mean_df: pd.DataFrame
    trimmed_df: pd.DataFrame
    kinetics_df: pd.DataFrame
    cd_pathlength_cm: float
    factor: float
    analysis_inputs: dict
    fingerprint: str
    basis: str = "strand"
    y_label: str = DELTA_EPS
    c_unmixed_uM: float = float("nan")      # strand concentration before mixing
    c_cell_uM: float = float("nan")         # ... and in the cell


def run_processing(files, settings):
    """All of sections 2 and 3 at once."""
    mean_df = average_traces(files, settings.chosen_columns)
    trimmed_df = trim(mean_df, settings.points_from_beginning, settings.points_from_end)
    l_cd = cd_pathlength_used(files, settings)
    factor = conversion_factor(settings, l_cd)
    kinetics_df = convert(trimmed_df, settings.baseline, factor)
    c_unmixed, c_cell = strand_concentrations(settings)
    inputs = {
        "Selected kinetics": [f"{column} (CSV file {index + 1})" for index, column in settings.chosen_columns],
        "Points removed from the beginning": settings.points_from_beginning,
        "Points removed from the end": settings.points_from_end,
        "Sequence (5'->3')": settings.sequence or "(not given)",
        "Sequence length (nt)": settings.sequence_length,
        "Extinction coefficient (M^-1 cm^-1 nt^-1)": settings.extinction_coefficient,
        "Extinction coefficient of the strand (M^-1 cm^-1)": settings.sequence_length * settings.extinction_coefficient,
        "Extinction coefficient source": ("nearest-neighbour method from the sequence (Gray et al. 1995, "
                                          "Methods Enzymol. 246, 19-34)"
                                          if settings.sequence else "entered / preset"),
        "Concentration from": ("absorbance (c = A / (N * epsilon * l))" if settings.concentration_source != "entered"
                               else "entered directly (" + ("in the cell, after mixing)" if settings.concentration_in_cell
                                                            else "before mixing)")),
        "Absorbance of the unmixed solution": (settings.absorbance if settings.concentration_source != "entered"
                                               else "(not used)"),
        "Path length of the absorbance measurement (cm)": (settings.absorbance_pathlength_cm
                                                           if settings.concentration_source != "entered"
                                                           else "(not used)"),
        "Strand concentration before mixing (uM)": c_unmixed * 1e6,
        "Strand concentration in the cell (uM)": c_cell * 1e6,
        "Path length of the CD measurement (cm)": l_cd,
        "Baseline (mdeg)": settings.baseline,
        "Delta epsilon expressed": DELTA_EPS_BASES.get(settings.delta_eps_basis, settings.delta_eps_basis),
        "Conversion factor (mdeg -> delta epsilon)": factor,
    }
    basis = "nucleotide" if settings.delta_eps_basis == "nucleotide" else "strand"
    return ProcessingResult(mean_df, trimmed_df, kinetics_df, l_cd, factor, inputs,
                            data_fingerprint(kinetics_df), basis, delta_eps_label(basis),
                            c_unmixed * 1e6, c_cell * 1e6)
