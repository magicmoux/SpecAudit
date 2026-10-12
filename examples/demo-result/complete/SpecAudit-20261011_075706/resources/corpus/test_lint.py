# Mechanical lint of bubble-sort.md: numbering, cross-references, delimiters.
import json, os, re
from pathlib import Path

DOC = "bubble-sort.md"


def doc():
    p = json.loads(os.environ.get("SPEC_DOCS", "{}")).get(DOC, DOC)
    return Path(p).read_text(encoding="utf-8")


LABEL = re.compile(r"\*\*(Definition|Algorithm|Lemma|Proposition|Corollary|Example|Theorem) (\d+)")
REF = re.compile(r"\b(Definition|Algorithm|Lemma|Proposition|Corollary|Example|Theorem) (\d+)")


def test_numbering_continuous_and_unique():
    nums = [int(m.group(2)) for m in LABEL.finditer(doc())]
    assert nums == list(range(1, len(nums) + 1)), nums


def test_cross_references_have_targets():
    text = doc()
    labels = {(m.group(1), m.group(2)) for m in LABEL.finditer(text)}
    refs = {(m.group(1), m.group(2)) for m in REF.finditer(text)}
    assert not (refs - labels), sorted(refs - labels)


KNOWN_MISSPELLINGS = ["comparisns", "algoritm", "permuation", "recieve", "occurence"]


def test_known_misspellings_absent():
    text = doc().lower()
    assert [w for w in KNOWN_MISSPELLINGS if w in text] == []


def test_example_6_shows_the_whole_pass():
    # a pass on (3, 1, 2) ends with (1, 2, 3); the example must say so
    L = [3, 1, 2]
    for j in range(1, 3):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    assert L == [1, 2, 3]
    assert "which gives (1, 2, 3)" in doc()


def test_conventions_stated_in_definition_1():
    # weak order and tracked entries: a precondition of the stability and ties statements
    text = doc()
    assert "in the weak sense (equal elements allowed)" in text
    assert "two equal entries remain two distinct elements" in text


def test_delimiters_balanced():
    text = doc()
    for o, c in ["()", "[]", "{}"]:
        assert text.count(o) == text.count(c), (o, c)
    assert text.count("**") % 2 == 0
