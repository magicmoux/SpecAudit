# Audit profiles (design)

Status: design. Only the first step is implemented: the rules specific to formal documents have moved to [`skills/start/profiles/formal.md`](../skills/start/profiles/formal.md), with no change in behavior. Everything else below is planned.

## Why profiles

SpecAudit's core does not depend on the domain: cold detection by fresh agents, triage, cause graph, bottom-up fixing, independent adjudication, guards written before the fix, suspects, worktree isolation, internal revisions, stop and resume, closing. What depends on the domain is what counts as an error, what counts as evidence, what a guard looks like, and which artifacts can decide a question.

Applied as is to a functional specification, a requirements document or a UI specification, the formal protocol would fail in two ways: most findings would end UNDECIDED, since "false statement" demands an executed counterexample that such documents rarely allow, and genuine defects (an untestable requirement, two contradictory screens) would be filed as form defects. A profile fixes those four points for a kind of document and leaves the core untouched.

## What a profile defines

One file per profile in `skills/start/profiles/`, read only when it applies. Every profile has the same sections, which the protocol refers to by name:

| Section | Content |
|---|---|
| Errors | taxonomy of the errors of that domain |
| Form defects | what goes to the editorial track instead |
| Inventory units | what the inventory lists (theorems, requirements, screens…) |
| Reviewer angles | the angles of the first wave |
| Oracles | kinds of artifacts that can decide a question, by strength |
| Evidence | levels of evidence, and what each level demands |
| Guards | form of the regression guards |
| Fixes | rules specific to fixing (for instance mapped statements) |
| Lint | mechanical checks of the editorial track |
| Resources | plugins, connectors or skills worth recommending, each with its role (see below) |

The agents stay generic: the profile's taxonomy, evidence levels and angles are passed in their message, as the oracle table is today. (Until the second profile exists, the agents keep the formal taxonomy in their own files.)

## Planned profiles

| Profile | Documents | Errors (examples) | Evidence | Guards |
|---|---|---|---|---|
| `formal` (done) | theory, proofs, algorithms, formal specifications | false statement, incomplete proof, insufficient scoping… | formal, model, ad hoc | theorems in the build, bounded checks |
| `functional` | functional specifications, requirements, statements of work | ambiguous, incomplete, untestable or contradictory requirement; requirement inconsistent with the code or another document; missing acceptance criterion | executed (a scenario replayed on the code or a prototype), model (a state machine or decision table checked by script), argued (a contradiction quoted on both sides) | acceptance tests (Gherkin), exhaustive decision tables, requirements ↔ tests traceability check |
| `ui` | screen, component and journey specifications | journey that dead-ends, state not specified, inconsistency with the mock-ups, accessibility rule broken | executed on a prototype (Playwright), compared with a mock-up snapshot, argued | journey tests, mock-up conformity checks |
| `research` | positioning, related work, prior art, bibliography | claim not supported by its source, missed prior art, inaccurate citation | quoted source (from the project's corpus of sources), argued | citation checks against the sources corpus |
| `experimental` | benchmark protocols and harnesses | protocol not reproducible, ill-defined metric, conclusion beyond the measurements | replayed with the harness | harness runs with fixed seeds |

A document may combine profiles: a main one, and sections under another (a "Related work" section of a formal paper under `research`).

## Choosing the profile

By order of precedence:

1. **`--profile <name>`** on the command, for a one-off audit.
2. **The project configuration**, `spec-audit/config.json`, versioned with the project, so that the choice is reviewed and the audit replayable:

   ```json
   {
     "profiles": {
       "observation-derivative-calculus*.md": "formal",
       "42.*_CANDIDATE_*.md": "formal",
       "4[04]_*.md": "research",
       "51_OUT_benchmark_harness.md": "experimental"
     },
     "resources": { "research": ["sources/"] }
   }
   ```

3. **A heuristic**, when nothing is configured, from signals in the document: theorem, lemma, proof, quantifiers → `formal`; numbered requirements (REQ-…), "shall / must", user stories, acceptance criteria → `functional`; screens, components, journeys, links to mock-ups → `ui`; dense citations, positioning, state of the art → `research`. The heuristic never decides alone: phase 0 proposes its result in one question, then writes the answer into `spec-audit/config.json`, so that the next audit does not ask again.

**Existing project or initial roadmap.** Both end in the same file. On an existing project, the first audit scans the documents and proposes a complete `config.json` for the user to validate. On a new project, the roadmap or initial plan declares which deliverable falls under which profile, and the configuration is written with it.

## Resources on demand

Plugins, connectors and skills can serve an audit, but never as live context in the audit session: they would bias the reviewers, and their answers are not reproducible. A resource enters an audit in one of three roles only:

| Role | Example | How it enters |
|---|---|---|
| **Frozen source** | a mock-up connector, a ticket tracker, a prior-art search service | the launcher queries it once, exports the content as files into the worktree with their SHA-256, and adds them to the oracle table |
| **Executable oracle** | a plugin providing a command-line checker, a journey test runner | its command joins the audit session's allow list, like `lake` today |
| **Normative reference** | a requirements writing guide, an internal standard | it becomes a declared normative dependency, given to the reviewers as a file |

A skill that only brings instructions or know-how fills none of these roles: it stays in the launcher's session, which may use it to produce an oracle (for instance to generate acceptance tests that then become a runner).

**Phase 0 flow, on the launcher's side, with the user:**

1. The profile lists its recommended resources (`ui`: mock-up connector, journey test runner, accessibility reference).
2. The launcher compares them with what is installed (`claude plugin list --json`, `claude mcp list`) and, in the desktop app, looks in the catalog for what is missing.
3. A multiple-choice question offers the recommended resources, with a free answer to add others; each chosen resource is given its role. The question tool takes 4 options at most: beyond that, group by role or ask several questions.
4. Installing a plugin or connecting a connector is an action the user confirms; the launcher never does it alone.
5. The resources kept, their role and the SHA-256 of the exports are recorded in the register and recalled in the report.

## Implementation steps

1. Move the formal rules into `profiles/formal.md`, with no change in behavior. **Done.**
2. Write `profiles/functional.md`; make the agents generic (taxonomy, evidence and angles passed in their message); add `--profile` and `spec-audit/config.json`.
3. Add the heuristic and the configuration proposal at phase 0.
4. Add the resources flow (frozen sources, executable oracles, normative references).
5. Write `research`, then `ui` and `experimental`, each tested on a real document of its domain.

## Open questions

- Should the `argued` evidence level be allowed to confirm an error alone, or only to escalate it to the user?
- How are frozen sources refreshed between two audits: a new export at each audit, or only on request?
- Can one audit mix documents of different profiles, or is it one profile per audit, as one register per document is today?
