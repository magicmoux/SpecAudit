#!/usr/bin/env python3
"""Select the use edges to probe for hypothesis discharge, and keep their results across audits.

  python3 discharge.py select <edges.json> <cache.json> --strongest formal|model|ad-hoc
  python3 discharge.py record <edges.json> <cache.json>

edges.json, written by the orchestrator at phase 0 (step 7) and kept up to date with the fixes:

  {
    "profile": "formal",
    "documents": ["selection.md"],
    "edges": [
      {"id": "E-1", "user": "Proposition 3", "used": "Lemma 2", "hypothesis": "x ≥ 0",
       "used_statement": "<exact quote>", "user_statement": "<exact quote>", "use_passage": "<exact quote>",
       "guarantee": "unstated" | "<exact quote of where the user guarantees the hypothesis>",
       "status": null, "oracle": null, "level": null}
    ]
  }

select checks that every quote is in the documents (whitespace ignored), computes each edge's key from the
profile and the four texts, and sets each edge's status:
  stated      the guarantee is quoted: not probed;
  needed, discharged, not_refuted
              settled by the cache for this key (cached: true); a not_refuted entry is reused only when its
              evidence level is at least the strongest level of the oracle table;
  to probe    everything else.
It prints the ids to probe. Exit code 1 when a quote is not found in the documents (the edge's text is then not
the document's, and its key would be meaningless), 2 on a malformed file.

record writes into the cache every edge whose status is needed, discharged or not_refuted, under the key of its
texts as they are now, with its oracle and evidence level. It computes the keys itself, so the orchestrator may
rewrite edges.json freely; what it must keep true is that a status describes the edge's current texts (reset it to
null when it updates the quotes of a probed edge, unless a confirmed error already settles the new texts). The cache
only grows; an entry whose key no edge has any more is kept, and simply never matches.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

LEVELS = {"ad hoc": 0, "ad-hoc": 0, "model": 1, "formal": 2}
FINAL = {"needed", "discharged"}
CACHED = FINAL | {"not_refuted"}
TEXTS = ("used_statement", "hypothesis", "user_statement", "use_passage")


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def key(profile, edge):
    return hashlib.sha256("\x1f".join([profile] + [norm(edge[t]) for t in TEXTS]).encode("utf-8")).hexdigest()


def load(path, default=None):
    p = Path(path)
    if not p.exists() and default is not None:
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"discharge: cannot read {path}: {e}")


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def select(edges_path, cache_path, strongest):
    data, cache = load(edges_path), load(cache_path, {})
    try:
        corpus = norm(" ".join(Path(d).read_text(encoding="utf-8") for d in data["documents"]))
        profile, edges = data["profile"], data["edges"]
    except (OSError, KeyError, TypeError) as e:
        print(f"discharge: malformed {edges_path}: {e}", file=sys.stderr)
        return 2
    missing = [f"{e['id']}: {t}" for e in edges for t in TEXTS + ("guarantee",)
               if t != "hypothesis" and e.get(t) not in (None, "unstated") and norm(e[t]) not in corpus]
    if missing:
        print("quotes not found in the documents:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    to_probe = []
    for e in edges:
        e["key"] = key(profile, e)
        hit = cache.get(e["key"])
        e["cached"] = False
        if e["guarantee"] != "unstated":
            e["status"] = "stated"
        elif hit and (hit["status"] in FINAL or LEVELS[hit["level"]] >= LEVELS[strongest]):
            e.update(status=hit["status"], oracle=hit["oracle"], level=hit["level"], cached=True)
        else:
            e["status"] = "to probe"
            to_probe.append(e["id"])
    save(edges_path, data)
    counts = {s: sum(e["status"] == s for e in edges) for s in ("stated", "to probe")}
    print(f"edges: {len(edges)}; stated: {counts['stated']}; from the cache: {sum(e['cached'] for e in edges)}; "
          f"to probe: {counts['to probe']}")
    print("to probe: " + (", ".join(to_probe) or "none"))
    return 0


def record(edges_path, cache_path):
    data, cache = load(edges_path), load(cache_path, {})
    n = 0
    for e in data.get("edges", []):
        if e.get("status") in CACHED:
            cache[key(data["profile"], e)] = {"status": e["status"], "oracle": e.get("oracle") or "none", "level": e["level"],
                               "user": e["user"], "used": e["used"], "hypothesis": e["hypothesis"],
                               "recorded": date.today().isoformat()}
            n += 1
    save(cache_path, cache)
    print(f"recorded: {n}; cache entries: {len(cache)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("edges"), s.add_argument("cache")
    s.add_argument("--strongest", required=True, choices=["formal", "model", "ad-hoc"])
    r = sub.add_parser("record")
    r.add_argument("edges"), r.add_argument("cache")
    a = ap.parse_args()
    return select(a.edges, a.cache, a.strongest) if a.cmd == "select" else record(a.edges, a.cache)


if __name__ == "__main__":
    sys.exit(main())
