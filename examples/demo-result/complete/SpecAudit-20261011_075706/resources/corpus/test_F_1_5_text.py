# Text guard F-1-5 — the Abstract and the Conclusion say that the passes of Algorithm 7 end earlier, not that they start later
import json, os
from pathlib import Path


def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")


def test_F_1_5_text():
    text = doc("bubble-sort.md")
    assert "passes start further and further into the list" not in text
    assert "starts each pass where the part of the list already sorted ends" not in text
    assert "passes end earlier and earlier in the list" in text
    assert "ends each pass where the part of the list already sorted begins" in text
