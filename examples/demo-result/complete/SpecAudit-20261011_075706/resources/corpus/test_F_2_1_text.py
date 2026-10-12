# Text guard F-2-1 — the proof of Lemma 3 ends by showing that Algorithm 2 sorts (i = n − 1, then position 1)
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_2_1_text():
    text = doc("bubble-sort.md")
    assert "For i = n − 1 (n ≥ 2), position 1 then holds the remaining element" in text
    assert "so Algorithm 2 sorts L" in text
