# Undecided statements (design)

Status: design, not implemented. Three mechanisms: splitting an undecided statement into cases, an attempt ledger that stops on method saturation, and a budget per item. Two more are left for later: a cache of attempts across audits, and a stop condition for an audit whose remaining items all wait on open cases.

## Why

Today, an error whose adjudicator can neither confirm nor refute it is UNDECIDED (4.1). It is relaunched once at the usual effort ("Escalation"), then escalated to the user, and its consequences and suspects stay BLOCKED to the end of the audit. That is the right answer for a short statement, and the wrong one for a hard one.

A real case: a theorem that no method could decide as stated. Adding constraints and hypotheses made three of its four cases provable. The fourth stayed undecided only because a person stopped after trying three or four proof methods and oracles, and much execution time. An automated audit has no such person. It stops only on its global budget, which fails three ways:

- **All or nothing.** The theorem is UNDECIDED as a whole, and its whole chain stays BLOCKED, although three cases are settled and most of its uses need only those.
- **No record of the effort.** "Undecided" does not say what was tried, so the next audit, or the reader, cannot tell a statement that resisted five methods from one that met a single timeout.
- **One item can eat the audit.** Nothing bounds the effort spent on one item but the budget of the whole audit, so a hard case starves every other item.

## 1. Splitting into cases

When an item stays UNDECIDED after its escalation, it is split into cases rather than escalated as a whole.

**Who splits.** The adjudicator proposes the split, in a `cases` field of its verdict: a partition of the statement's domain by conditions, each condition stated with the definitions and hypotheses of the document, and for each case what it found (proof, counterexample, nothing). The orchestrator does not invent the cases: choosing them is a judgment on the statement, which it must not make on a text it may have fixed itself.

**Each case is an item.** A case `F-k-n.c` is verified like an error (4.1): by a fresh adjudicator, on `HEAD`, one at a time, its verdict recorded with its revision. It is CONFIRMED (a counterexample in that case), HOLDS (a proof, or the strongest evidence the profile accepts), or UNDECIDED, and then follows the attempt ledger (2) and its budget (3).

**Settlement.**
- A case CONFIRMED false makes the item a confirmed error, with that counterexample, on the usual path (4.2 to 4.4).
- Cases that hold, with others undecided, give a **scoping addition** (4.3): the statement restricted to the cases that hold, the weakest statement known to be true. The undecided cases are not deleted: they are stated as open in the document, next to the result, so that the restriction does not silently withdraw a claim ("never delete a result silently").
- If the statement is a main result, this restriction changes what the document claims: it is a critical fix (4.3), presented to the user, or left pending in a non-interactive session. The report then gives it ready to apply: proved in cases 1 to 3, case 4 open.

**Consequences.** Propagation (4.4) treats the restriction as any scoping addition: every use must satisfy the new condition. A use that falls in the cases that hold is reassessed (4.5) and can be RESOLVED. A use that needs an open case stays BLOCKED, by that case alone, not by the whole statement.

**Is the partition exhaustive?** For the restated result it need not be: the restriction claims only the cases that hold. For the report it must be said: the adjudicator states whether its cases cover the whole domain, with the check it ran (an exhaustive enumeration on a bounded domain, or a proof), and the report flags a partition that does not.

**Guards.** Each case that holds gets the usual guards (4.2), and the text guard asserts the restated statement. An open case gets no guard of its own; its ledger (2) records the furthest bound explored.

## 2. Attempt ledger and method saturation

Every attempt on an undecided item or case is recorded, and the attempts stop when the methods are exhausted, not when the budget is.

**Ledger.** In the item's entry of the register, one row per attempt: the agent, the revision, the **method family**, the oracle and its parameters, the time used, the outcome (counterexample, proof, timeout, inconclusive) and the progress made, if any.

**Method families** are listed by the profile, in a new `Method families` section. For `formal`: exhaustive enumeration on a bounded domain; random or property-based search; SAT or SMT solving; proof in a proof assistant; model checking; symbolic computation. Two attempts in the same family with other parameters are the same family.

**Each new attempt changes family.** A fresh adjudicator receives the item, the families already tried (their names only), and the facts already established with executed evidence (a lemma proved and checked, the bound up to which an exhaustive search found no counterexample). It does not receive the earlier adjudicators' reasoning, which would steer it into the same dead end. It is asked to use a family not yet tried, or to extend an established fact, a larger bound for instance.

**Progress** is a fact that did not hold before the attempt: a case closed, a lemma proved and checked, a bound raised, a class of counterexamples excluded with evidence. A rewording, a plan or a partial argument is not progress.

**Stop rule: saturation.** Attempts on an item stop when at least *k* distinct families have been tried (default 3) and the last *m* attempts (default 2) made no progress. The item then becomes **OPEN (saturated)**. The rule cuts both ways: an item still making progress goes on even when its attempts are many, and a saturated item stops even when budget is left. It is the same idea as detection, which stops when a wave brings nothing new.

**Environment failures do not count.** An attempt that could not run (a tool refused, an interpreter missing) is an environment problem (4.1): it is fixed, and the attempt does not count toward saturation.

The ledger turns "undecided" into a claim a reader can check: "three families, six attempts, exhaustive up to n = 7, no progress in the last two".

## 3. A budget per item

Each item gets its own budget, so that no item can spend the audit's.

**What is counted** is what the orchestrator observes as it goes: the number of attempts, and the oracle time per attempt and in total. Tokens are measured only afterwards (`consumption.py`), so they are reported per item, not used to stop.

**How much.** By severity: higher for a critical item or a main result, lower for a minor one. Defaults in the profile; overridden by the project configuration (`defaults: item-attempts`, `item-oracle-time`) or the command.

**Reached before saturation**, the item becomes **OPEN (budget reached)**, with its ledger. The report keeps it apart from a saturated item: more effort might still settle it, which "Run another check" can give, with a larger budget.

**Effect on the audit.** An OPEN item, and the uses that need its open cases, stay BLOCKED; the audit goes on with every other item, one at a time as always. Within the same audit, an OPEN item is not tried again unless a fix changes its text.

The global budget (`--max-passes`, the usage threshold) still applies; the per-item budget only keeps one item from spending it.

## Statuses

| Status | Meaning |
|---|---|
| UNDECIDED | not settled yet: attempts may follow |
| OPEN (saturated) | *k* families tried, no progress in the last *m* attempts |
| OPEN (budget reached) | the item's budget ran out while attempts still progressed |
| HOLDS | for a case: proved, or established at the strongest evidence level the profile accepts |

An OPEN item is listed in the report's "Open points" with its cases, its ledger in short, and what would settle it; in the summary of issues it is a P2 row, or P1 when a claim of the abstract or the conclusion depends on it.

## Place in the protocol

- 4.1: an UNDECIDED verdict after escalation leads to the split into cases, then to the ledger, instead of a direct escalation to the user.
- 4.3 and 4.4: the restriction to the cases that hold is a scoping addition, critical for a main result; propagation and reassessment follow it.
- `references/register.md`: a `Cases` table and an `Attempts` table in the error entry; the new statuses.
- `references/report.md`: open cases, ledgers and the exhaustiveness of each partition in "Open points" and "Scope of verification".
- Profile: a `Method families` section, and default budgets per severity.
- `agents/spec-adjudicator.md`: the `cases` field, the method family of each attempt, the progress made, and the instruction to change family.
- Parameters and configuration: `item-attempts`, `item-oracle-time`, and *k* and *m*.
- Unchanged: one agent at a time, each on the current revision; an attempt is one adjudicator.

## Open questions

- The defaults for *k*, *m* and the budgets, to calibrate on real documents rather than the demo.
- How much of the established facts to give a new attempt without steering it: a proved lemma is evidence, but naming it already points at an approach.
- Whether a case may be split again, and how deep.
- The cache of attempts across audits, keyed on the statement and the case like `discharge.json`, and a stop condition for an audit whose remaining items all wait on OPEN cases: left for after this design.
