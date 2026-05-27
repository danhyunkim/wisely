"""Unit tests for whitelist.normalize()."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from whitelist import normalize


def test_401k_lowercase():
    match, conf = normalize("401k")
    assert match == "401(k)"
    assert conf >= 80


def test_401_space_k():
    match, conf = normalize("401 K")
    assert match == "401(k)"
    assert conf >= 80


def test_roth_ira_exact():
    match, conf = normalize("Roth IRA")
    assert match == "Roth IRA"
    assert conf == 100


def test_whole_life_policy():
    match, conf = normalize("Whole Life Policy")
    assert match == "Whole Life"
    assert conf >= 80


def test_random_gibberish():
    assert normalize("Random gibberish xyz") == (None, 0)
