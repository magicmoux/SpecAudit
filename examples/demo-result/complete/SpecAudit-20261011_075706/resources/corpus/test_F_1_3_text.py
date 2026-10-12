# Text guard F-1-3 — Corollary 5 lets the i-th pass end at n − i + 1, not start at i
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_3_text():
    text = doc("bubble-sort.md")
    assert "the i-th pass can start at position i instead of position 1" not in text
    assert "positions 1 to i − 1 already hold their final elements" not in text
    assert "the i-th pass can end at position n − i + 1 instead of position n" in text
