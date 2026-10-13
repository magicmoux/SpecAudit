# Example: bubble sort

[`demo/bubble-sort.md`](demo/bubble-sort.md) is a short specification, barely a page long, of bubble sort and a variant meant to be faster. It deliberately contains errors: a cause, the chain of consequences it entails, an independent error and two form defects, next to correct statements that look suspicious. Any developer can check them by hand, and the audit checks them by running the algorithms. It lets you watch a complete audit in a few minutes, at no risk to your own documents.

## Try it

The audit needs a git repository and creates its worktree next to it. Prepare a throwaway repository:

```bash
mkdir spec-audit-demo
cd spec-audit-demo
git init
curl -O https://raw.githubusercontent.com/magicmoux/SpecAudit/main/examples/demo/bubble-sort.md
git add bubble-sort.md
git commit -m "Demo specification"
claude
```

(From a clone of the repository, replace `curl` with a copy of `examples/demo/bubble-sort.md`.)

Then, in Claude Code, describe the project's architecture (accept the proposal: `bubble-sort.md` audited, with the `formal` profile, and let it commit the file), then audit:

```text
/spec-audit:init
/spec-audit:start bubble-sort.md --max-passes 2
```

The worktree is created in `../spec-audit-demo-audit-bubble-sort`, on the branch `audit/bubble-sort`. The guards, in Python, are written to `spec-guards/`.

## What the audit should find

Read this section after the audit, to compare with its report.

<details>
<summary>Planted errors and defects</summary>

| Passage | Nature | Witness | Place in the graph |
|---|---|---|---|
| Lemma 3: after pass i, the i smallest elements occupy positions 1 to i | false statement: a small element moves left by at most one position per pass; it is the i largest that reach their place, at the end | L = (2, 3, 1): after the first pass, (2, 1, 3) | root |
| Corollary 5: pass i can start at position i | false statement, inherited from Lemma 3 | L = (2, 3, 1): starting pass 2 at position 2 leaves (2, 1, 3) | consequence of Lemma 3 |
| Correctness of Algorithm 7: "the same list as Algorithm 2, hence L sorted" | false claim, inherited from Corollary 5 | L = (2, 3, 1): Algorithm 7 returns (2, 1, 3) | consequence of Corollary 5 |
| Abstract and Conclusion: passes that "start further and further into the list" sort any list | false claim about Algorithm 7, which they name | same | consequences of the same chain |
| Example 6: the first pass gives (1, 3, 2) | wrong computed example: the pass stops after its first comparison | L = (3, 1, 2): the first pass gives (1, 2, 3) | independent root |
| Correctness of Algorithm 7: "Corollary 8" | form defect: cross-reference to a nonexistent result (Corollary 5) | — | editorial track |
| Correctness of Algorithm 7: "comparisns" | form defect: typo | — | editorial track |

Algorithm 2, Proposition 4 (stability of any sequence of passes, which holds because a pass swaps only on a strict inequality, so it covers Algorithm 7 too) and the count of comparisons, n(n − 1)/2 for Algorithm 7, are correct: a fix that changed them would be an over-correction. The expected minimal fix of Lemma 3 is "the i largest elements of L occupy positions n − i + 1 to n", after which the consequences are fixed in turn: pass i can stop at position n − i + 1, and Algorithm 7 makes its passes from position 1 to position n − i + 1, with the same count of comparisons.

If the reviewers miss a link of this chain — say the Abstract — it still enters the graph: once the correctness claim of Algorithm 7 is confirmed, the passages that use it, Abstract and Conclusion, become suspects (origin `suspect (uses F-…)`), blocked until the claim is fixed, then reassessed against the fixed text.

The fix of the Abstract and the Conclusion changes what the document claims, so it is a critical fix: it waits for your approval, while Lemma 3 itself is fixed as the cause. Hence two typical endings:

| Run | Outcome | Results folder |
|---|---|---|
| `/spec-audit:start bubble-sort.md --max-passes 1` | partial, needs decision: the critical fix is pending | `SpecAudit-…/` without a fixed copy; the partly fixed document is in `resources/bubble-sort.partial.md` |
| `/spec-audit:start bubble-sort.md --auto --max-passes 2` | every confirmed error fixed | `SpecAudit-…/bubble-sort.fixed.md` beside `source/bubble-sort.md` |

The results of two real runs, one of each kind, are in [demo-result/](demo-result/README.md), as files: compare them with yours, or replay their checks with Python alone.

Then, from the results folder, `python3 resources/replay.py --on source` shows each fixed error's text guard red on the original, and `--on fixed` every guard green; `/spec-audit:attest` reports the folder as not attested and gives the command to sign it.

The reviewers may also raise genuine but unplanted gaps: the proof of Lemma 3 is an induction whose hypothesis is never stated, and Algorithm 2 makes n − 1 passes without saying why that is enough.

</details>

# Example: hypothesis discharge

[`discharge/block-search.md`](discharge/block-search.md) specifies a membership search over sorted blocks. Each statement reads well, and each proof is one line that applies the previous result. The flaw lies in the use of one result by another, not in any statement taken alone. This is what hypothesis discharge looks for ([design](../docs/hypothesis-discharge.md)).

Prepare a throwaway repository as above with `block-search.md`, then:

```text
/spec-audit:start block-search.md --max-passes 2
```

<details>
<summary>What the audit should find</summary>

| Passage | Nature | Witness | Place in the graph |
|---|---|---|---|
| Proposition 3: applies Lemma 2 to A ++ B | insufficient scoping: Lemma 2 needs a sorted list, and A ++ B is not sorted when an element of A exceeds one of B | A = (3), B = (1, 2), v = 3: binary search on (3, 1, 2) returns false | root, found by the probe of the edge Proposition 3 → Lemma 2 |
| Theorem 6, Abstract, Conclusion | false claim, inherited: Algorithm 5 concatenates the blocks and searches once | blocks (3) and (1, 2), v = 3 | consequences, added at once by lifting the probe's counterexample |

Lemma 2 is correct: the fix belongs to its use, not to the lemma. Proposition 4 makes the same use correctly, since its hypothesis makes A ++ B sorted. Its probe settles by a quote, and a fix that changed it would be an over-correction. Example 7 is correct, and so is Corollary 8: it applies Proposition 4 to the two halves of a sorted list, whose hypothesis holds by an argument rather than a quote, so its edge is probed and found no counterexample. That result is the one a second audit reuses from the cache. The fix of Theorem 6 changes what the abstract claims, so it is a critical fix and waits for your approval, or is applied with `--auto`.

The probes are recorded in the corpus, in `spec-guards/discharge.json`. A second audit of the same document probes again only the edges whose texts changed.

</details>
