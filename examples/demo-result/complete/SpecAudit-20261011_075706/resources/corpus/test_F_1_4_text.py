# Text guard F-1-4 — Algorithm 7 makes pass i from position 1 to n − i + 1 and cites Corollary 5
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_4_text():
    text = doc("bubble-sort.md")
    assert "make a pass from position i to position n" not in text
    assert "By Corollary 8" not in text
    assert "make a pass from position 1 to position n − i + 1" in text
    assert "By Corollary 5, Algorithm 7 returns the same list as Algorithm 2" in text
