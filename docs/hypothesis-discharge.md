# Hypothesis discharge (design)

Status: implemented, not yet validated on a real document. The protocol is in [`skills/start/references/discharge.md`](../skills/start/references/discharge.md), the selection and the cache in [`discharge.py`](../skills/start/references/discharge.py), the probe in the `spec-adjudicator` agent; `--no-discharge` turns it off.

## Why

The cause graph (phase 3) links errors that reviewers have already found, and fixing runs bottom-up from its roots (phase 4). An error of the most common kind in formal documents slips through this: a result P applies a lemma N without guaranteeing one of N's hypotheses H. N is correct, P reads as correct, and no reviewer flags either. Even when the error is found, it is found on a consequence, and reaching its root takes as many fixing rounds as the chain is long.

Hypothesis discharge checks every use edge of the document directly: when P applies N, does P's context guarantee each hypothesis of N? Each answer is a probe, which can expose a counterexample of P and carry it up the chain to its root.

## Dependency graph

The inventory (phase 0, step 7) already lists every unit with its statement and the units it uses. It needs one addition: for each use `P → N`, the hypotheses of N that the use relies on, and where P guarantees each one (a hypothesis of P, an earlier step of its proof, a definition), or `unstated` when nothing in P does.

This graph is built on the initial version of the document, before any fix. It is a graph of statements, unlike the cause graph, which is a graph of errors.

## Probe

A probe asks one question about one edge `P → N` and one hypothesis H of N: is there an input that satisfies P's hypotheses, violates H, and falsifies P's conclusion?

- The probe is built **under P's hypotheses**. A counterexample that P's hypotheses already exclude proves only that N needs H, which is normal; it is not an error.
- The probe is executed, on the strongest oracle of the project (the register's oracle table), like an adjudicator's counterexample.
- An executed counterexample is a concrete object that satisfies every other hypothesis, so it also proves that dropping H introduces no contradiction: no separate consistency check is needed.
- A probe is a disposable test. It enters the corpus only as a guard, once its error is confirmed (4.2).

**Red probe.** P needs H and does not guarantee it. The probe opens a candidate error on P, which goes through triage (phase 2) and a fresh adjudicator (4.1) like any other. Only once that error is CONFIRMED are P's uses marked as suspects; a red probe alone never marks anything, since a badly built probe would make a whole subtree suspect for nothing.

**Lifting.** If P is itself applied by Q, rerun the same counterexample under Q's hypotheses, against Q's conclusion. While it stays red, the counterexample climbs the dependency tree toward the main results. In the cause graph the error stays on P, its cause, and every result reached is one of its consequences: the whole chain is known at once, without waiting for the bottom-up rounds of phase 4, and the highest result reached tells whether a main result is at stake. Lifting costs one execution per level.

**Green probe.** No counterexample was found. This is evidence of a different strength depending on the oracle (below), and it goes to the cache.

## Asymmetry of the results

A counterexample proves that a hypothesis is needed. The absence of a counterexample does not prove that it is not needed: it proves only that this oracle, with this budget, found none. The cache keeps the two apart:

| Status | Meaning | Reuse |
|---|---|---|
| `needed` | executed counterexample under P's hypotheses | final, as long as the key holds |
| `discharged` | P guarantees H, shown by a proof or a mechanized oracle | final, as long as the key holds |
| `not_refuted@<oracle>` | no counterexample found by that oracle | a hint only: reprobed when a stronger oracle covers the edge |

## Cache across versions

One entry per triple (P, N, H), stored in the corpus (`<corpus>/discharge.json`), so that it travels with the document on the audit's branch, outlives the audit and serves the next version. The corpus rather than the project configuration: reviewers never read it, and a project configured by `.specaudit.md` alone would otherwise need a `.specaudit/` folder too.

The key is a hash of the profile and of four texts, whitespace normalized: N's statement, H, P's statement, and the passage of P that applies N. The oracle is not in the key: the entry records the level searched, and `not_refuted` is reused only while the oracle table has nothing stronger. An entry is invalidated as soon as one of these changes, P's side included: rewording P can remove the guarantee of H even if N is untouched. An audit of a new version therefore reprobes only the edges that the diff touches.

## Cost

The main cost is the number of edges times the number of hypotheses. Three filters keep it low:

1. One agent reads the extended inventory and keeps only the hypotheses marked `unstated`; an explicitly guaranteed hypothesis is not probed.
2. The cache removes the edges already settled for this key.
3. Lifting reuses the counterexample already written: climbing costs executions, not new agents.

## Place in the protocol

- Phase 0, step 7: with the inventory, `edges.json` records the hypotheses of each use and how P guarantees them, by exact quotes; `discharge.py select` refuses a quote not found in the document, so that keys are stable from one audit to the next.
- Phase 1: probes after the reviewers' waves, on the same revision, one at a time, by a fresh `spec-adjudicator` per use at `medium` effort; their red results are findings for phase 2, with origin `probe (E-…)`, or `probe (lifted from E-…)` for the results reached by lifting.
- Phase 3: the cause graph takes the edges established by lifting.
- Phases 4.3 and 4.4: a fix updates the quotes of its edges, and a scoping addition adds an edge for each use of the result; right after the fix's commit, before the next error is verified, `select` returns the edges whose texts changed, and they are probed at once, on that revision. `select` keeps the status of an edge already settled in the audit while its texts are unchanged, so a re-probe touches only what the fix changed.
- Phase 6: `discharge.py record` writes the iteration's settled probes into the cache, committed with the iteration.

## Open questions

- Which oracle strength may mark an edge `discharged` for each profile, and whether `not_refuted` entries should expire.
- Whether a hypothesis that turns out not needed at all (P's conclusion holds without it) should be reported as a form defect, since the statement could be weakened.
- How to normalize statements for the cache key so that a pure rewording does not invalidate it, without letting a change of meaning through. For now only whitespace is normalized: any rewording reprobes, which costs probes but never reuses a stale result.
