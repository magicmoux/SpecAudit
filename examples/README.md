# Example: incremental selection

[`demo/selection.md`](demo/selection.md) is a short specification, barely a page long, that deliberately contains errors: a cause, the chain of consequences it entails, an independent error and two form defects. It lets you watch a complete audit in a few minutes, at no risk to your own documents.

## Try it

The audit needs a git repository and creates its worktree next to it. Prepare a throwaway repository:

```bash
mkdir spec-audit-demo
cd spec-audit-demo
git init
curl -O https://raw.githubusercontent.com/magicmoux/SpecAudit/main/examples/demo/selection.md
git add selection.md
git commit -m "Demo specification"
claude
```

(From a clone of the repository, replace `curl` with a copy of `examples/demo/selection.md`.)

Then, in Claude Code:

```text
/spec-audit:spec-audit selection.md --max-iter 2
```

The worktree is created in `../spec-audit-demo-audit-selection`, on the branch `audit/selection`. The guards, in Python, are written to `spec-guards/`.

## What the audit should find

Read this section after the audit, to compare with its report.

<details>
<summary>Planted errors and defects</summary>

| Passage | Nature | Witness | Place in the graph |
|---|---|---|---|
| Lemma 3: \|P_k(L)\| = k | false statement: ignores the case k > n | k = 3, L = (1, 2): \|P_3(L)\| = 2 | root |
| Corollary 5: \|P_k(L ++ M)\| = k | false statement, inherited from Lemma 3 | k = 3, L = (1), M = (2) | consequence of Lemma 3 |
| Correctness of Algorithm 7: "exactly k elements" | false claim, inherited from Corollary 5 | k = 3, blocks (2) then (1): R = (1, 2) | consequence of Corollary 5 |
| Abstract and Conclusion | claim more than the body proves | same | consequences of the same chain |
| Example 6: P_2(L) = (1, 4) | wrong computed example: duplicates | L = (5, 1, 4, 1): P_2(L) = (1, 1) | independent root |
| Correctness of Algorithm 7: "Corollary 8" | form defect: cross-reference to a nonexistent result (Corollary 5) | — | editorial track |
| Correctness of Algorithm 7: "elemnts" | form defect: typo | — | editorial track |

Proposition 4 and the output of Algorithm 7 are correct: a fix that changed them would be an over-correction. The expected minimal fix of Lemma 3 is |P_k(L)| = min(k, |L|), or the added hypothesis k ≤ |L|, after which the consequences are fixed in turn.

If the reviewers miss a link of this chain — say the Abstract — it still enters the graph: once the correctness claim of Algorithm 7 is confirmed, the passages that use it, Abstract and Conclusion, become suspects (origin `suspect (uses F-…)`), blocked until the claim is fixed, then reassessed against the fixed text.

The reviewers may also raise genuine but unplanted proof gaps: the handling of duplicates in the proof of Proposition 4, or the idempotence P_k(P_k(L)) = P_k(L), used without being stated in the correctness argument of Algorithm 7.

</details>
