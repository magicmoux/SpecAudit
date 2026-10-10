---
description: Stops the spec-audit launched from this session. Stops its audit session, or interrupts its subagents, reports its last internal revision, marked incomplete, then asks whether to suspend the audit, keep that revision as the new base, or cancel the audit.
disable-model-invocation: true
argument-hint: "[<document>]"
---

# Stop the audit launched from this session

An audit can only be stopped from the session that launched it. Another session knows neither the step in progress nor the process or agents running, and it could remove a worktree while the audit is still writing to it.

1. **Find the audit.** This session owns one if an audit was started here (`/spec-audit:start`) and its register is in your context. Otherwise, if `$ARGUMENTS` names a document, find its worktree (`git worktree list`, branch `audit/<slug>`) and read `spec-audit/<slug>/register.md` there:
   - if its session is not `${CLAUDE_SESSION_ID}`, change nothing: say that the audit belongs to session <session> (named `[AUDIT] <slug>` when it could be renamed) and must be stopped from there;
   - if its mode is an audit session (process id and session id in the register) and that process is still alive, the audit runs in that process, even if your conversation was cleared: stop it as 8.9 says;
   - if its session is this one but the audit is no longer in your context (cleared conversation) and no such process is alive, the audit is no longer running: set its state to `suspended`, and say that `--resume` continues it;
   - if its state is already `suspended` or `closed`, say so.

   If no audit is found, say so and stop.
2. **Stop it.** Follow "8.9 Stop on request" of the start skill (`/spec-audit:start`). In the default mode, that begins by stopping the audit session's process. The stop report lists the interrupted agents and their scratch directories: at resume they are replaced by fresh agents that reuse those directories, never resumed.
