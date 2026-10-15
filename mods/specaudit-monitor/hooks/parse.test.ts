import { describe, expect, test } from 'claude-code/testing'

import { auditWorktrees, bar, controlsOf, indexSection, isLive, limitAlerts, listErrors, marginUsed, parsePauseAt, parseRegister, stageOf } from './parse'

const REGISTER = `# Audit register — selection.md

- Document(s): selection.md
- Corpus: spec-guards/, runner: \`python run_guards.py\`
- Worktree: C:/Temp/sa-e2e-audit-selection, branch audit/20261015_175354, base 2e88756; final commit (at closing)
- Scratch root: C:/Temp/sa-e2e-audit-selection-scratch/
- Interpreter: python (python3 is the Microsoft Store stub); paths: native
- Preflight: passed, attempt 1 of 3
- Parameters: max-passes = 1, auto = no, fail-fast = no, pause-at = session=7,week=25, auto-resume = no, model = sonnet
- Session: 705774c1, state: running
- Resumes: 0
- Mode: audit session (pid 1660, session 3b98458e)

## Agents

| Name | Role | Error or wave | Effort | Revision | Scratch | State |
|---|---|---|---|---|---|---|
| a-F-1-1 | adjudicator | F-1-1 | medium | \`5696540\` | iter-1/a | done |
| a-F-1-2 | adjudicator | F-1-2 | medium | \`5696540\` | iter-1/b | running |

## Iteration log

| Iter. | Detection waves |
|---|---|
| 1 | 3 |

## Internal revisions

| Rev. | Commit |
|---|---|
| r1 | abc |
| r2 | def |

## Errors

### F-1-1 — Lemma 3 ignores n < k
- **Status**: FIXED (r3)
- **Type**: false statement; **Severity**: major (lemma)
- **Proposed fix** (scoping addition, not applied): use min(k, n)

### F-1-2 — Example 6 miscomputed
- **Status**: DETECTED

### F-1-3 — Proposition 4
- **Origin**: reviewer; **Status**: REFUTED; **Type**: false statement

### F-1-4 — Corollary 5
- **Status**: BLOCKED (by F-1-1)

## Form defects
`

describe('register', () => {
  test('header fields', async () => {
    const info = parseRegister(REGISTER)
    expect(info.document).toBe('selection.md')
    expect(info.branch).toBe('audit/20261015_175354')
    expect(info.base).toBe('2e88756')
    expect(info.corpus).toBe('spec-guards/')
    expect(info.scratch).toBe('C:/Temp/sa-e2e-audit-selection-scratch')
    expect(info.interpreter).toBe('python')
    expect(info.pauseAt).toEqual({ session: 0.07, week: 0.25 })
    expect(info.iterations).toBe(1)
    expect(info.revisions).toBe(2)
  })

  test('errors counted by status, evaluated leaves out DETECTED and BLOCKED', async () => {
    const c = parseRegister(REGISTER).counts
    expect(c.total).toBe(4)
    expect(c.evaluated).toBe(2)
    expect(c.fixed).toBe(1)
    expect(c.confirmed).toBe(1)
    expect(c.refuted).toBe(1)
    expect(c.blocked).toBe(1)
  })

  test('the running agent and the stage', async () => {
    const info = parseRegister(REGISTER)
    expect(info.agent).toBe('adjudicator F-1-2')
    expect(info.agentsDone).toBe(1)
    expect(isLive(info)).toBe(true)
    expect(stageOf(info)).toBe('Agent : adjudicator F-1-2')
  })

  test('a paused and a closed audit', async () => {
    const paused = parseRegister(
      REGISTER.replace('state: running', 'state: suspended (usage limit: week, resumes 2026-10-18 01:05:00)'),
    )
    expect(stageOf(paused)).toBe("En pause, limite d'usage (reprise 2026-10-18 01:05:00)")
    const orphaned = parseRegister(REGISTER.replace('state: running', 'state: suspended (launcher session deleted)'))
    expect(stageOf(orphaned)).toBe('Suspendu, session de lancement supprimée')
    const closed = parseRegister(REGISTER.replace('state: running', 'state: closed'))
    expect(isLive(closed)).toBe(false)
    expect(stageOf(closed)).toBe('Terminé')
  })

  test('the launcher, the mode, and the controls they allow', async () => {
    const info = parseRegister(REGISTER)
    expect(info.launcher).toBe('705774c1')
    expect(info.inProcess).toBe(true)
    const snap = (state: string, extra = {}) => ({
      project: 'demo', stamp: 's', isLive: !state.startsWith('closed'), stage: '', state, updatedAt: 0,
      scratch: 'C:/x-scratch', launcher: '705774c1', inProcess: true, ...extra,
    })
    expect(controlsOf(snap('running'))).toEqual({ canPause: true, canStop: true, canResume: false })
    expect(controlsOf(snap('running', { stopRequested: true }))).toEqual({ canPause: false, canStop: false, canResume: false })
    expect(controlsOf(snap('suspended (stopped on request)'))).toEqual({ canPause: false, canStop: false, canResume: true })
    expect(controlsOf(snap('running', { inProcess: false }))).toEqual({ canPause: false, canStop: false, canResume: false })
    expect(controlsOf(snap('closed'))).toEqual({ canPause: false, canStop: false, canResume: false })
    expect(parseRegister(REGISTER.replace(/^- Mode: .*$/m, '- Mode: in session')).inProcess).toBe(false)
  })

  test('limit alerts from 70 % of the margin, an error from 90 %', async () => {
    const snap = (session: number, week: number, isLive = true) => ({
      project: 'demo', isLive, stage: '', updatedAt: 0,
      session: { start: 0.1, now: session, limit: 0.2 }, week: { start: 0.2, now: week, limit: 0.3 },
    })
    expect(limitAlerts(snap(0.15, 0.2))).toEqual([])
    expect(limitAlerts(snap(0.18, 0.2)).map(a => [a.name, a.tone])).toEqual([['5 h', 'warning']])
    expect(limitAlerts(snap(0.18, 0.3)).map(a => [a.name, a.tone])).toEqual([['5 h', 'warning'], ['semaine', 'error']])
    expect(limitAlerts(snap(0.2, 0.3, false))).toEqual([])
  })

  test('each error with its id, title and status', async () => {
    const rows = listErrors(REGISTER)
    expect(rows.length).toBe(4)
    expect(rows[0].id).toBe('F-1-1')
    expect(rows[0].title).toBe('Lemma 3 ignores n < k')
    expect(rows[0].status).toBe('FIXED (r3)')
    expect(rows[0].type).toBe('false statement')
    expect(rows[0].severity).toBe('major (lemma)')
    expect(rows[0].fix).toBe('(scoping addition, not applied) use min(k, n)')
    expect(rows[3].status).toBe('BLOCKED (by F-1-1)')
    expect(rows[2].status).toBe('REFUTED')
  })

  test('pause-at defaults and forms', async () => {
    expect(parsePauseAt('- Parameters: max-passes = 1')).toEqual({ session: 0.75, week: 0.5 })
    expect(parsePauseAt('- Parameters: pause-at = 80, auto-resume = no')).toEqual({ session: 0.8, week: 0.8 })
  })
})

describe('git and index', () => {
  test('audit worktrees only', async () => {
    const porcelain = [
      'worktree D:/Repos/p\nHEAD 1\nbranch refs/heads/master',
      'worktree D:/Repos/p-audit-x\nHEAD 2\nbranch refs/heads/audit/20261015_175354',
    ].join('\n\n')
    expect(auditWorktrees(porcelain)).toEqual([{ path: 'D:/Repos/p-audit-x', stamp: '20261015_175354' }])
  })

  test('index section as a map', async () => {
    const index = `## SpecAudit-20261015_175354

| | |
|---|---|
| Result | FINISHED — Partial, needs decision |
| Consumption | 6.38 M tokens, $2.10 |
`
    const section = indexSection(index, '20261015_175354')
    expect(section['Result']).toBe('FINISHED — Partial, needs decision')
    expect(section['Consumption']).toBe('6.38 M tokens, $2.10')
  })
})

describe('margin', () => {
  test('from the use at launch to the pause threshold', async () => {
    expect(Math.round(marginUsed({ start: 0.2, now: 0.22, limit: 0.25 }) * 100)).toBe(40)
    expect(marginUsed({ start: 0.2, now: 0.3, limit: 0.25 })).toBe(1)
    expect(bar(0.5, 4)).toBe('██░░')
  })
})
