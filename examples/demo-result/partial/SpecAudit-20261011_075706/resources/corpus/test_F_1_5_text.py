# Text guard F-1-5 — Example 6 gives the true result of the whole first pass
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_5_text():
    text = doc("bubble-sort.md")
    assert "which gives (1, 3, 2).\n" not in text
    assert "so the pass returns (1, 2, 3)" in text
