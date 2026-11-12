# tests/test_extinction.py
"""The extinction coefficient from the sequence gives the values of the original
stand-alone calculator by J. Palacký that it was ported from (reference values computed with it)."""

import pytest

from src.modules.analysis.extinction import SequenceError, compute_ext_coeff, extinction

# sequence -> compute_ext_coeff(sequence) of the earlier stand-alone calculator
REFERENCE = {
    "GGGTTAGGGTTAGGGTTAGGG": 10641.0,
    "TTGGGTTGGGTTTGGGTTGGGTT": 9623.5,
    "AGGGTTAGGGTTAGGGTTAGGGTT": 10570.0,
    "GGGTTGGGTTGGGTTGGG": 10014.4,
    "ACGTACGTAC": 10198.0,
    "AUGCAUGC": 10072.5,
    "GGXGTIACC": 9957.5,          # X left out, I counted as G
    "AT": 11420.0,
}


@pytest.mark.parametrize("seq,value", REFERENCE.items())
def test_same_as_original_script(seq, value):
    assert compute_ext_coeff(seq) == value


def test_per_nucleotide_and_strand():
    r = extinction("5'-GGG TTA GGG TTA GGG TTA GGG-3'")          # spaces, dashes, 5'/3' ignored
    assert r.sequence == "GGGTTAGGGTTAGGGTTAGGG" and r.length == 21
    assert r.epsilon_per_nt == 10641.0
    assert r.epsilon_strand == pytest.approx(10641.0 * 21, abs=1)


def test_abasic_site_keeps_the_strand_value():
    r = extinction("GGXGTIACC")
    assert r.length == 9 and r.counted == 8
    # length x ε per nt = the strand ε of the original (8 counted positions x 9957.5)
    assert r.length * r.epsilon_per_nt == pytest.approx(8 * 9957.5, abs=1)


def test_lower_case_and_single_nucleotide():
    assert extinction("gggtta").sequence == "GGGTTA"
    assert extinction("A").epsilon_per_nt == 15340.0


@pytest.mark.parametrize("bad", ["", "XXX", "GGGNTTA", "GGG TT B"])
def test_invalid(bad):
    with pytest.raises(SequenceError):
        extinction(bad)
