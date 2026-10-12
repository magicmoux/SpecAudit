# Text guard F-1-1 — Lemma 3 states the i largest elements, at the end of the list, not the i smallest at the start
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_1_text():
    text = doc("bubble-sort.md")
    assert "the i smallest elements of L occupy positions 1 to i" not in text
    assert "the i largest elements of L occupy positions n − i + 1 to n" in text
