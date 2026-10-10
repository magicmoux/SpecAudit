---
name: stop
description: Stops the spec-audit running in this session. Interrupts its subagents, reports its last internal revision, marked incomplete, then asks whether to suspend the audit, keep that revision as the new base, or cancel the audit.
disable-model-invocation: true
argument-hint: "[<document>]"
---

# Stop the audit running in this session

An audit can only be stopped from the session that runs it. Another session knows neither the step in progress nor the agents running, and it could remove a worktree while the audit is still writing to it.

1. **Find the audit.** This session runs one if the spec-audit skill was invoked here and its register is in your context. Otherwise, if `$ARGUMENTS` names a document, find its worktree (`git worktree list`, branch `audit/<slug>`) and read `spec-audit/<slug>/register.md` there:
   - if its session is not `${CLAUDE_SESSION_ID}`, change nothing: say that the audit runs in session <session> (named `[AUDIT] <slug>` when it could be renamed) and must be stopped from there;
   - if its session is this one but the audit is no longer in your context (cleared conversation), the audit is no longer running: set its state to `suspended`, and say that `--resume` continues it;
   - if its state is already `suspended` or `closed`, say so.

   If no audit is found, say so and stop.
2. **Stop it.** Follow "8.9 Stop on request" of the spec-audit skill.
