# Hypothesis discharge

Part of `/spec-audit:start`, whose folder is `skills/start/` of the plugin (`SKILL.md` gives its full path as `${CLAUDE_SKILL_DIR}`, which a file read afterwards does not substitute: below, `${CLAUDE_SKILL_DIR}` means that folder). Read by the orchestrator at phase 1 of each iteration, and kept for the re-probes after each fix (4.4), unless `--no-discharge` is given. The terms (inventory, oracle table, register, suspects, scratch root) are those of `SKILL.md`; the design is in the plugin's `docs/hypothesis-discharge.md`.

A result P that applies a result N without guaranteeing one of N's hypotheses H reads as correct, and so does N: no reviewer flags either, and when the error is found at last, it is found on a consequence, as many fixing rounds away from its cause as the chain is long. Hypothesis discharge asks the question on every use edge directly, by an executed probe.

## Edges

`spec-audit/<slug>/edges.json`, written at phase 0, step 7, with the inventory: one edge per use `P → N` and per hypothesis H of N that the use relies on, with exact quotes from the document (format in `discharge.py`). `guarantee` quotes where P guarantees H (a hypothesis of P, an earlier step of its proof, a definition), or is `unstated` when nothing in P does. Mark `unstated` whenever the guarantee would take an argument rather than a quote: the probe decides those, not your reading.

Keep it in step with the document: when a fix changes a statement or a proof (4.3), update the quotes of its edges and reset their status to null, unless a confirmed error already settles the new texts (a use that does not guarantee a hypothesis just added to N is `needed`); and when a scoping addition gives N a new hypothesis (4.4), add an edge for each use of N. These updates go in the fix's internal revision, and the edges whose texts changed are probed again right after it ("Re-probe after a fix"), not at the next iteration. A status always describes the edge's texts as they are now: that is what `record` caches.

## Select

At phase 1, once the reviewers' waves are done, on the revision they read:

`<python> <scratch root>/protocol/discharge.py select spec-audit/<slug>/edges.json <corpus>/discharge.json --strongest <formal|model|ad-hoc>`

(with `--in-session`: `<python> ${CLAUDE_SKILL_DIR}/references/discharge.py …`), where `--strongest` is the strongest level of the oracle table, `ad-hoc` when it has no oracle. The cache, `<corpus>/discharge.json`, holds the probes of earlier audits and iterations, keyed on the texts of each edge: an edge whose texts have not changed since it was settled is not probed again, and neither is an edge already settled in this audit (its status in `edges.json`) while its texts are those it was settled on. A quote not found in the document stops `select`: correct the quote in `edges.json`, never the document.

**Re-probe after a fix.** Right after the commit of an internal revision (4.3), before the next item is verified (4.4, "After the commit"), run `select` again, on that revision: it returns exactly the edges whose texts the fix changed or added. Probe them as below, one at a time, each launched on that revision. A RED verdict goes to triage and the cause graph at once, so that the next item is chosen with it in the graph; waiting for the next iteration would let the audit verify, and fix, results above an edge already known to be at stake.

## Probes

For each edge `to probe`, launch a fresh `spec-adjudicator` at `medium` effort ("Effort per step"), one at a time ("One agent at a time"), on `HEAD`, its revision recorded in the agent table and with its verdict; one agent takes every edge of the same use `P → N`, since they share P's context. Name it `audit-<slug>-probe-<E-…>`, record it in the agent table, and give it only this:

```
Probe of a use edge in <document paths>.
User: <P, location and quote of its statement>.
Used: <N, location and quote of its statement>.
Hypothesis of N relied on: <H> (edge <E-…>).
Results above the user, in order, each applying the previous one: <Q, R… with location and quote, from the inventory, up to the results that nothing else uses; or "none">.
Oracle table: <of the register>.
Scratch directory: <scratch root>/iter-<k>/probe-<E-…>.
Return the probe block of your output format.
```

Nothing about the audit, the reviewers' findings or the register: like a reviewer, a prober told where others looked looks there too.

## Verdicts

Record `select`'s summary and one row per probed edge in the register's section `Hypothesis discharge — iteration <k>` (format in `references/register.md`), as each verdict arrives: the section is what the report counts, and what a `--resume` reads to know which probes are done.

Check a RED verdict as you check a confirmation (4.1, "Evidence"): its `script` exists in the scratch directory and its `output` shows P's conclusion failing; a RED whose counterexample was evaluated by hand is UNDECIDED.

| Verdict | Meaning | Status of the edge | Then |
|---|---|---|---|
| `RED` | an executed input satisfies P's hypotheses, violates H, and falsifies P's conclusion | `red` | a finding for phase 2: an error on P, of type insufficient scoping or false statement, origin `probe (E-…)`, with the counterexample as its witness; and, for each result in `lifted` that the counterexample also falsifies, a finding on it, origin `probe (lifted from E-…)`, its probable cause being the error on P |
| `DISCHARGED` | P guarantees H, by a quote or a proof run on a formal oracle | `discharged` | nothing to fix; if the guarantee is a quote, correct `guarantee` in `edges.json` |
| `GREEN` | no counterexample found | `not_refuted`, with the level searched | nothing to fix |
| `UNDECIDED` | the probe could not conclude (execution refused, search inconclusive) | unchanged | relaunch once at the usual effort ("Escalation"); then record it in the register and leave it |

A RED probe proposes an error; it does not confirm one. Its finding goes through triage (phase 2) and a fresh adjudicator (4.1) like a reviewer's, so that an ill-built probe makes nothing suspect: the uses of P become suspects only once the error on P is CONFIRMED. Once it is, set the edge to `needed`; if the error is REFUTED, set the edge to `refuted` and record why in the register: `select` does not probe it again while its texts are unchanged, since triage would discard the same finding (phase 2), and a fix that changes them probes it again.

**Lifting.** The prober reruns its counterexample, carried through each application, against the results above P, in order, and stops at the first one it does not falsify. Every result it reaches is a consequence of the error on P: in phase 3, add the edges `P → Q → …` at once, justified by "same counterexample, lifted by probe E-…", instead of discovering them one fixing round at a time (4.4). The highest result reached tells, before any fix, whether a main result is at stake (critical fixes, 4.3).

## Record

At the end of each iteration (phase 6), before its commit:

`<python> <scratch root>/protocol/discharge.py record spec-audit/<slug>/edges.json <corpus>/discharge.json`

and stage `<corpus>/discharge.json` with the iteration's files. Run it even when no probe was settled: the file then records nothing new, and its presence tells the next audit that discharge ran. The cache belongs to the corpus: it travels with the document on the audit's branch, and the next audit of the same document reprobes only the edges a change has touched.
