import type { Counts, ErrorRow } from '../types'

// Reads SpecAudit's own files (skills/start/references/register.md gives their format). Pure functions: no `$`.

export type RegisterInfo = {
  document?: string
  worktree?: string
  branch?: string
  base?: string
  corpus?: string
  scratch?: string
  interpreter: string
  state?: string
  preflight?: string
  pauseAt: { session: number; week: number }
  resumes?: number
  counts: Counts
  agent?: string
  agentsDone: number
  agentsTotal: number
  iterations: number
  revisions: number
  hasClosing: boolean
}

const field = (text: string, re: RegExp) => re.exec(text)?.[1]?.trim()

/** The rows of the first Markdown table under `## <title>`, header and separator dropped, cells trimmed. */
export function tableRows(text: string, title: string): string[][] {
  const at = text.search(new RegExp(`^## ${title}\\b`, 'm'))
  if (at < 0) return []
  const rest = text.slice(at).split('\n').slice(1)
  const end = rest.findIndex(line => line.startsWith('## '))
  const lines = (end < 0 ? rest : rest.slice(0, end)).filter(line => line.startsWith('|'))
  return lines
    .slice(2)
    .map(line => line.slice(1, line.trimEnd().endsWith('|') ? line.trimEnd().length - 1 : undefined).split(' | ').map(c => c.trim()))
}

/** pause-at as the register records it: `session=7,week=25`, `80`, or `off`; SpecAudit's defaults otherwise. */
export function parsePauseAt(text: string): { session: number; week: number } {
  const spec = field(text, /pause-at = ([\w=.,]+?)(?:, [a-z-]+ =|\s*$)/m)
  const out = { session: 0.75, week: 0.5 }
  if (!spec || spec === 'off') return spec === 'off' ? { session: 1, week: 1 } : out
  if (!spec.includes('=')) return { session: Number(spec) / 100, week: Number(spec) / 100 }
  for (const part of spec.split(',')) {
    const [name, value] = part.split('=')
    if (name === 'session' || name === 'week') out[name] = Number(value) / 100
  }
  return out
}

export function countErrors(text: string): Counts {
  const counts: Counts = { total: 0, evaluated: 0, confirmed: 0, fixed: 0, refuted: 0, resolved: 0, undecided: 0, blocked: 0 }
  const at = text.search(/^## Errors\b/m)
  if (at < 0) return counts
  const rest = text.slice(at + 1)
  const section = rest.slice(0, rest.search(/^## /m) < 0 ? undefined : rest.search(/^## /m))
  for (const entry of section.split(/^### /m).slice(1)) {
    const status = /\*\*Status\*\*: ([A-Z]+)/.exec(entry)?.[1] ?? 'DETECTED'
    counts.total += 1
    if (status !== 'DETECTED' && status !== 'BLOCKED') counts.evaluated += 1
    if (status === 'CONFIRMED' || status === 'FIXED' || status === 'RECURRENCE') counts.confirmed += 1
    if (status === 'FIXED') counts.fixed += 1
    if (status === 'REFUTED') counts.refuted += 1
    if (status === 'RESOLVED') counts.resolved += 1
    if (status === 'UNDECIDED' || status === 'ESCALATED') counts.undecided += 1
    if (status === 'BLOCKED') counts.blocked += 1
  }
  return counts
}

/**
 * One field of an error entry, `**Name**: value` or `**Name** (note): value`, up to the next field on its line or the
 * line's end; cut at 280 characters, what a hover card shows.
 */
export function entryField(entry: string, name: string): string | undefined {
  const re = new RegExp(`\\*\\*${name}\\*\\*(?: \\(([^)]*)\\))?: (.+?)\\s*(?:;\\s*\\*\\*|$)`, 'm')
  const m = re.exec(entry)
  if (!m) return undefined
  const value = (m[1] ? `(${m[1]}) ` : '') + m[2].trim()
  return value.length > 280 ? `${value.slice(0, 279)}…` : value
}

/** Each error entry: its id, its title, and its status with what follows it (`FIXED (r3)`, `BLOCKED (by F-1-1)`). */
export function listErrors(text: string): ErrorRow[] {
  const at = text.search(/^## Errors\b/m)
  if (at < 0) return []
  const rest = text.slice(at + 1)
  const end = rest.search(/^## /m)
  return (end < 0 ? rest : rest.slice(0, end))
    .split(/^### /m)
    .slice(1)
    .map(entry => {
      const head = /^(F-[\w.-]+)\s*[—-]\s*(.*)$/m.exec(entry)
      const fix = entryField(entry, 'Fix') ?? entryField(entry, 'Proposed fix')
      return {
        id: head?.[1] ?? '?',
        title: head?.[2]?.trim() ?? '',
        status: entryField(entry, 'Status') ?? 'DETECTED',
        type: entryField(entry, 'Type'),
        severity: entryField(entry, 'Severity'),
        causes: entryField(entry, 'Causes'),
        location: entryField(entry, 'Location'),
        evidence: entryField(entry, 'Evidence'),
        guards: entryField(entry, 'Guards'),
        fix,
      }
    })
}

export function parseRegister(text: string): RegisterInfo {
  const worktree = /^- Worktree: (.+?), branch (\S+?),? base ([0-9a-f]+)/m.exec(text)
  const agents = tableRows(text, 'Agents')
  const running = agents.filter(row => !(row[6] ?? '').startsWith('done'))
  const last = running[running.length - 1]
  return {
    document: field(text, /^- Document\(s\): (.+)$/m),
    worktree: worktree?.[1],
    branch: worktree?.[2],
    base: worktree?.[3],
    corpus: field(text, /^- Corpus: ([^,\s]+)/m),
    scratch: field(text, /^- Scratch root: (\S+)/m)?.replace(/[\\/]+$/, ''),
    interpreter: field(text, /^- Interpreter: (\S+)/m) ?? 'python',
    state: field(text, /^- Session: .*?state: (.+)$/m),
    preflight: field(text, /^- Preflight: ([^,.;]+)/m),
    pauseAt: parsePauseAt(text),
    resumes: Number(field(text, /^- Resumes: (\d+)/m) ?? 0),
    counts: countErrors(text),
    agent: last ? `${last[1]} ${last[2]}`.trim() : undefined,
    agentsDone: agents.length - running.length,
    agentsTotal: agents.length,
    iterations: tableRows(text, 'Iteration log').length,
    revisions: tableRows(text, 'Internal revisions').length,
    hasClosing: /^## Closing\b/m.test(text),
  }
}

/** Whether the audit's session is still going: anything but `closed`. */
export const isLive = (info: RegisterInfo) => !!info.state && !info.state.startsWith('closed')

export function stageOf(info: RegisterInfo): string {
  const state = info.state ?? ''
  if (state.startsWith('closed')) return 'Terminé'
  if (state.startsWith('suspended (usage limit')) {
    const until = /resumes ([^)]+)\)/.exec(state)?.[1]
    return `En pause, limite d'usage${until ? ` (reprise ${until})` : ''}`
  }
  if (state.startsWith('suspended')) return 'Suspendu'
  if (state.startsWith('stopping')) return 'Arrêt en cours'
  if (info.hasClosing) return 'Clôture'
  if (info.preflight?.startsWith('in progress')) return 'Préflight'
  if (info.agent) return `Agent : ${info.agent}`
  if (info.counts.total === 0) return 'Détection'
  return info.counts.evaluated < info.counts.total ? 'Vérification' : 'Corrections et passes'
}

/** The audit/<stamp> worktrees `git worktree list --porcelain` names. */
export function auditWorktrees(porcelain: string): { path: string; stamp: string }[] {
  return porcelain
    .split(/\r?\n\r?\n/)
    .map(block => ({
      path: /^worktree (.+)$/m.exec(block)?.[1]?.trim(),
      stamp: /^branch refs\/heads\/audit\/(\S+)$/m.exec(block)?.[1],
    }))
    .filter((w): w is { path: string; stamp: string } => !!w.path && !!w.stamp)
}

/** The section of one audit in SPECAUDITS.md, as `{ key: value }` from its table. */
export function indexSection(text: string, stamp: string): Record<string, string> {
  const at = text.indexOf(`## SpecAudit-${stamp}`)
  if (at < 0) return {}
  const rest = text.slice(at).split('\n').slice(1)
  const end = rest.findIndex(line => line.startsWith('## '))
  const out: Record<string, string> = {}
  for (const line of end < 0 ? rest : rest.slice(0, end)) {
    const cells = /^\| ([^|]+?) \| (.+?) \|\s*$/.exec(line)
    if (cells && cells[1] !== ' ' && !cells[1].startsWith('-')) out[cells[1].trim()] = cells[2].trim()
  }
  return out
}

/** A fraction of the margin the audit was given on a window: from its use at launch to its pause threshold. */
export function marginUsed(w: { now: number; start: number; limit: number }): number {
  const room = w.limit - w.start
  if (room <= 0) return 1
  return Math.max(0, Math.min(1, (w.now - w.start) / room))
}

export const bar = (fraction: number, width: number) => {
  const n = Math.round(Math.max(0, Math.min(1, fraction)) * width)
  return '█'.repeat(n) + '░'.repeat(width - n)
}

export const compact = (n: number) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(2)} M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)} k` : String(n)
