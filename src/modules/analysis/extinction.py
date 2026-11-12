# src/modules/analysis/extinction.py
"""Molar extinction coefficient of an oligonucleotide from its sequence (260 nm,
nearest-neighbour method), implemented by J. Palacký, following

    Gray D.M., Hung S.H., Johnson K.H. (1995) Absorption and circular dichroism
    spectroscopy of nucleic acid duplexes and triplexes.
    Methods Enzymol. 246, 19-34. doi:10.1016/0076-6879(95)46005-5

    ε_strand = 2 · Σ ε(nearest-neighbour doublets) − Σ ε(internal mononucleotides)

(twice the sum over all overlapping doublets, minus the mononucleotides except
the two terminal ones; the doublet values are per nucleotide).

The result is given per nucleotide, ε_nt = ε_strand / N, which is the value
the conversion to Δε needs (the strand ε is N · ε_nt).

As in J. Palacký's earlier stand-alone calculator (of which this is a port):
- abasic sites (X) are left out of the calculation,
- inosine (I) is counted as guanosine (G),
- DNA and RNA letters can be mixed; a T–U or U–T pair contributes 0.

Two small additions to that calculator: spaces, dashes, digits and the 5'/3' marks are ignored
(sequences are often written "5'-GGG TTA GGG-3'"), and a single nucleotide gets
its own ε (the original gives 0 there)."""

import re
from dataclasses import dataclass

MONONUCLEOTIDE = {"g": 12160, "a": 15340, "t": 8700, "c": 7600, "u": 10210}
DINUCLEOTIDE = {
    "aa": 13650, "ac": 10670, "ag": 12790, "at": 11420, "au": 12140,
    "ca": 10670, "cc": 7520, "cg": 9390, "ct": 7660, "cu": 8370,
    "ga": 12920, "gc": 9190, "gg": 11430, "gt": 10220, "gu": 10960,
    "ta": 11780, "tc": 8150, "tg": 9700, "tt": 8610,
    "ua": 12520, "uc": 8900, "ug": 10400, "uu": 10110,
    "tu": 0, "ut": 0,
}
ALLOWED = set("ACGTUIX")
_IGNORED = re.compile(r"[\s\-_'’′,.;:0-9]+")


class SequenceError(ValueError):
    pass


@dataclass
class ExtinctionResult:
    sequence: str            # cleaned, upper case, as entered (with X and I)
    length: int              # all positions, abasic sites included
    counted: int             # positions in the calculation (abasic sites left out)
    epsilon_strand: float    # M⁻¹ cm⁻¹
    epsilon_per_nt: float    # M⁻¹ cm⁻¹ nt⁻¹, = epsilon_strand / length (rounded to 0.1)


def clean_sequence(text):
    """Upper-case letters only; raises SequenceError for letters other than A C G T U I X."""
    seq = _IGNORED.sub("", text or "").upper()
    bad = sorted(set(seq) - ALLOWED)
    if bad:
        raise SequenceError(f"Unknown letter(s) {', '.join(bad)} - use A, C, G, T, U, "
                            f"I (inosine) and X (abasic site).")
    return seq


def strand_epsilon(sequence):
    """ε of the strand (M⁻¹ cm⁻¹), nearest-neighbour method; `sequence` already cleaned."""
    s = sequence.replace("X", "").replace("I", "G").lower()
    if not s:
        return 0.0
    if len(s) == 1:
        return float(MONONUCLEOTIDE[s])
    pairs = sum(DINUCLEOTIDE[s[i:i + 2]] for i in range(len(s) - 1))
    internal = sum(MONONUCLEOTIDE[c] for c in s[1:-1])
    return float(2 * pairs - internal)


def compute_ext_coeff(sequence):
    """As the earlier calculator: ε per nucleotide of the non-abasic positions, rounded to 0.1."""
    seq = clean_sequence(sequence)
    counted = len(seq.replace("X", ""))
    return round(strand_epsilon(seq) / counted, 1) if counted else 0


def extinction(text):
    """The sequence as typed -> ExtinctionResult (raises SequenceError)."""
    seq = clean_sequence(text)
    if not seq:
        raise SequenceError("Empty sequence.")
    counted = len(seq.replace("X", ""))
    if counted == 0:
        raise SequenceError("The sequence contains only abasic sites (X).")
    eps = strand_epsilon(seq)
    return ExtinctionResult(sequence=seq, length=len(seq), counted=counted, epsilon_strand=eps,
                            epsilon_per_nt=round(eps / len(seq), 1))
