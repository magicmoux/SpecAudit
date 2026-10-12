# Text guard F-1-2 — Corollary 5 lets the i-th pass stop at n − i + 1, not start at i
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_2_text():
    text = doc("bubble-sort.md")
    assert "the i-th pass can start at position i instead of position 1" not in text
    assert "the i-th pass can stop at position n − i + 1 instead of position n" in text
