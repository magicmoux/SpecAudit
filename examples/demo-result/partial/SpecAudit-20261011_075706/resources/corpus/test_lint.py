# Mechanical lint of bubble-sort.md: numbering, cross-references, math delimiters.
import json, os, re
from pathlib import Path

def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")

TEXT = doc("bubble-sort.md")
KINDS = ("Definition", "Algorithm", "Lemma", "Proposition", "Corollary", "Example", "Theorem")

def declared():
    return [int(m) for m in re.findall(r"^\*\*(?:%s) (\d+)" % "|".join(KINDS), TEXT, re.M)]

def test_numbering_continuous_and_unique():
    nums = declared()
    assert nums == list(range(1, len(nums) + 1)), nums

def test_cross_references_resolve():
    nums = set(declared())
    refs = re.findall(r"\b(?:%s) (\d+)" % "|".join(KINDS), TEXT)
    missing = sorted({int(r) for r in refs} - nums)
    assert not missing, missing

def test_known_misspellings_absent():  # D-1-2
    assert "comparisns" not in TEXT


def test_math_delimiters_balanced():
    for a, b in ("()", "[]", "{}"):
        assert TEXT.count(a) == TEXT.count(b), (a, b)
