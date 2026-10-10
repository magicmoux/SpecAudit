# Profile: formal

For documents whose content is mathematical, logical, algorithmic or theoretical: definitions, statements, proofs, algorithms, formal specifications of protocols or formats. SpecAudit was built on this profile; the protocol of `SKILL.md` refers to its sections by name.

## Errors

An **error** is a defect in the content specific to the document's domain (logical, mathematical, algorithmic, theoretical):

- a false statement (a counterexample exists);
- an invalid or incomplete proof;
- insufficient scoping: missing hypothesis, context or domain of application not restricted, edge case not handled;
- a definition that is inconsistent, ill-founded, or ambiguous enough to change a result;
- an algorithm that does not meet its specification, termination not guaranteed, a wrong complexity;
- two results that contradict each other, or an abstract, introduction or conclusion that claims more than the body proves;
- a wrong formula or computed example, even from a typo, since the meaning changes.

## Form defects

Typo outside formulas, numbering, cross-reference, bibliography entry. Any change to a formula, a symbol, an index, a quantifier or an inequality is an error, not a form defect: the meaning changes.

## Inventory units

Every definition, lemma, proposition, theorem and algorithm, with its statement and the results it uses.

## Reviewer angles

`full`, `logic and proofs`, `definitions, scoping and edge cases`, `algorithms and complexity`.

## Oracles

Artifacts that can decide statements of the document, by strength:

- **formal**: a mechanized development (Lean: `lakefile.toml` or `lakefile.lean` and `lean-toolchain`; Coq, Isabelle, Agda likewise). Its coverage comes from the document's own correspondence table when it has one (for instance a "Lean theorems / results" table), otherwise from its README;
- **model**: a reference model or brute-force checker (`verification/`, `model`, scripts the document names);
- **runner**: a test runner (`pytest`, `cargo test`, `mvn test`, a `run_*.py`), with the engines reachable from it (SQLite, DuckDB).

## Evidence

The adjudicator confirms with the strongest oracle of the table that covers the statement, and says which:

1. **formal**: the statement has a counterpart in a mechanized development of the project (the document's correspondence table says which theorem or definition). The counterexample is executed on that formal statement: by evaluation or decision (`#eval`, `decide`, an exhaustive enumeration on a bounded instance type), by a property-based search (Plausible or its equivalent), or as a theorem refuting the statement on a witness. A script that re-encodes the statement confirms nothing at this level: the encoding, not the text, would be judged.
2. **model**: a reference model or checker of the project covers the statement; the counterexample runs on it.
3. **ad hoc**: no oracle covers the statement; the adjudicator's own script, in exact arithmetic, run with its output recorded.

At every level the counterexample is executed, never evaluated by hand, however small: a hand evaluation repeats the reading that produced the report and can repeat its mistake, while a run is checked by the machine and replayable. A confirmation without a script and its output is treated as UNDECIDED.

The level is recorded in the register (`Evidence`). A statement of level 1 confirmed at level 3 stays UNDECIDED, with "a formal counterexample" as what would settle it; a statement of level 2 confirmed at level 3 is CONFIRMED but flagged. The final report counts confirmations by level.

## Guards

- Exact arithmetic (integers, rationals, symbolic computation), never equality between floats; fixed seeds.
- A guard is written for the oracle that confirmed the error, at its level: for a formal oracle, a theorem or a decided check in a module that the project's build compiles, so that replaying the corpus is the build (Lean example in `references/register.md`); for a model, a test that runs the model; otherwise a test of the runner (Python example in `references/register.md`). "Red first" then means that the theorem refuting the original statement on the witness compiles, and "green" that the fixed statement is re-proved, or passes its bounded check, in the same build. A decision procedure that extends the trusted base (`native_decide`) serves the search, never the recorded guard.

## Fixes

**Mapped statements**: when the fixed statement has a counterpart in a mechanized development (evidence level 1), the fix includes the change of the formal statement and of its proof, and the update of the correspondence table, in the same internal revision. Without them the error stays at "incomplete proof", never FIXED: the text would claim what the development no longer proves.

## Lint

Continuity and uniqueness of numbering, existence of the target of each cross-reference, presence of each cited key in the bibliography and citation of each entry, balance of math delimiters, symbols used before their definition when detectable.
