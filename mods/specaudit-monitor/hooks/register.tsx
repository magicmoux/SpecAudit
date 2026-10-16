import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { AuditLine, ErrorRow, Snapshot, Window } from '../types'
import {
  auditKey,
  auditWorktrees,
  bar,
  compact,
  controlsOf,
  deadOf,
  indexSection,
  isLive,
  limitAlerts,
  listErrors,
  marginUsed,
  parseRegister,
  pickAudit,
  stageOf,
  uniqueAudits,
} from './parse'

const PANE = 'specaudit'
const snapshot = atom({ plugin: 'specaudit-monitor', key: 'snapshot' } as const, null)
const tick = atom({ plugin: 'specaudit-monitor', key: 'tick' } as const, 0)
const unfolded = atom({ plugin: 'specaudit-monitor', key: 'unfolded' } as const, [])
const opened = atom({ plugin: 'specaudit-monitor', key: 'opened' } as const, [])
const armed = atom({ plugin: 'specaudit-monitor', key: 'armed' } as const, 0)
const selected = atom({ plugin: 'specaudit-monitor', key: 'selected' } as const, '')

// One tick a second turns the band's spinner; a live audit is
// read every 10 s, otherwise every 20 s, so that an
// audit launched meanwhile, or a change of folder, shows soon.
const TICK_MS = 1000
const LIVE_EVERY = 10
const IDLE_EVERY = 20
const SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

type Probe = {
  session: { start: number; now: number; resetsAt?: number } | null
  week: { start: number; now: number; resetsAt?: number } | null
  turns: number
  tokens: number
  cost: number
}

// The icon: a magnifying glass over the end-of-proof square, skeptical review and established proof. Teal reads on
// both themes; the desktop draws an Svg as an image, so it cannot take the text's color.
const ICON_COLOR = '#2A9D8F'
const ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><circle cx="6.5" cy="6.5" r="4.75" fill="none" stroke="${ICON_COLOR}" stroke-width="1.5"/><rect x="4.75" y="4.75" width="3.5" height="3.5" fill="${ICON_COLOR}"/><path d="M10.2 10.2L14.5 14.5" stroke="${ICON_COLOR}" stroke-width="2" stroke-linecap="round"/></svg>`

const slash = (p: string) => p.replace(/\\/g, '/').replace(/\/+$/, '')
const baseName = (p: string) => slash(p).split('/').pop() ?? p

// The root of the repository of the audit shown: the session's (its cwd's top level), or that of an audit
// ~/.specaudit/audits.json lists, when the person selected it, or when it is the livelier or the newer.
let cwd = ''

async function run($: EngineInterface, argv: string[], dir = cwd) {
  try {
    const out = await $.process.run(argv, { cwd: dir, timeoutMs: 20000 })
    return out.exitCode === 0 ? out.stdout : undefined
  } catch {
    return undefined
  }
}

async function readText($: EngineInterface, path: string) {
  try {
    return await $.fs.read(path)
  } catch {
    return undefined
  }
}

/** The registers of a repository's audits: every audit worktree's, live or ended, and its newest results folder's. */
async function registersOf($: EngineInterface, repo: string) {
  const found: { stamp: string; path: string }[] = []
  for (const wt of auditWorktrees((await run($, ['git', 'worktree', 'list', '--porcelain'], repo)) ?? '')) {
    const dir = `${slash(wt.path)}/spec-audit`
    const docs = await $.fs.list(dir).catch(() => [])
    for (const doc of docs) {
      if (doc.kind === 'dir' && (await $.fs.exists(`${dir}/${doc.name}/register.md`))) {
        found.push({ stamp: wt.stamp, path: `${dir}/${doc.name}/register.md` })
      }
    }
  }
  const results = (await $.fs.list(repo).catch(() => []))
    .map(entry => /^SpecAudit-(\d{8}_\d{6})$/.exec(entry.name)?.[1])
    .filter((stamp): stamp is string => !!stamp && !found.some(f => f.stamp === stamp))
    .sort((a, b) => b.localeCompare(a))
  for (const stamp of results) {
    const path = `${slash(repo)}/SpecAudit-${stamp}/register.md`
    if (await $.fs.exists(path)) {
      found.push({ stamp, path })
      break
    }
  }
  return found
}

// The interpreter that ran audits.py, found once: `python3` is a stub on Windows, and trying it again at every poll
// would change nothing. When none runs, the search waits for a day, or for a new audit of the session's repository,
// whose register names an interpreter that works.
const RETRY_MS = 24 * 3600 * 1000
let python: string | undefined
let failed: { at: number; stamp?: string } | undefined

/** One audit ~/.specaudit/audits.json lists (index.py writes it), or the old beacon's, which has no register. */
type Listed = { repo: string; stamp?: string | null; register?: string | null; results?: string; state?: string; updatedAt?: number }

/** The audits index.py recorded on this machine, as audits.py prints them; none when no interpreter runs it. */
async function listed($: EngineInterface, dir: string, audit?: { stamp: string; interpreter?: string }): Promise<Listed[]> {
  if (failed && failed.stamp === audit?.stamp && Date.now() - failed.at < RETRY_MS) return []
  const candidates = python ? [python] : [...new Set([audit?.interpreter, 'python3', 'python'].filter((c): c is string => !!c))]
  for (const candidate of candidates) {
    const out = await run($, [candidate, '-I', `${$.plugin.root}/hooks/audits.py`], dir)
    if (out === undefined) continue
    python = candidate
    failed = undefined
    try {
      const audits = out.trim() ? (JSON.parse(out) as { audits?: unknown }).audits : []
      return Array.isArray(audits) ? audits.filter((a): a is Listed => !!a && typeof a.repo === 'string' && !!a.repo) : []
    } catch {
      return []
    }
  }
  python = undefined
  failed = { at: Date.now(), stamp: audit?.stamp }
  return []
}

// The processes running, `<pid> <command line>` per line, read at most every 10 s, the pace of a live audit's refresh:
// whether an audit's process, or its launcher's, still runs. Undefined when they cannot be listed: the register's state is then taken as it is.
const PROCESSES_MS = 10000
let processCache: { at: number; lines: string[] | undefined } | undefined

async function processes($: EngineInterface) {
  if (processCache && Date.now() - processCache.at < PROCESSES_MS) return processCache.lines
  const windows = [
    'powershell',
    '-NoProfile',
    '-NonInteractive',
    '-Command',
    'Get-CimInstance Win32_Process | ForEach-Object { "$($_.ProcessId) $($_.CommandLine)" }',
  ]
  const posix = ['ps', '-eo', 'pid=,args=']
  const order = /^[A-Za-z]:/.test(cwd) ? [windows, posix] : [posix, windows]
  let lines: string[] | undefined
  for (const argv of order) {
    const out = await run($, argv)
    if (out) {
      lines = out.split(/\r?\n/).filter(Boolean)
      break
    }
  }
  processCache = { at: Date.now(), lines }
  return lines
}

type Found = {
  key: string
  repo: string
  stamp: string
  path: string
  text: string
  info: ReturnType<typeof parseRegister>
  live: boolean
  stopped?: string
  interpreter?: string
}

/** One audit read from its register, live while its register says so and its process (or launcher) still runs. */
async function load($: EngineInterface, repo: string, stamp: string, path: string): Promise<Found | undefined> {
  const text = await readText($, path)
  if (text === undefined) return undefined
  const info = parseRegister(text)
  const stopped = isLive(info) ? deadOf(info, await processes($)) : undefined
  return { key: auditKey(repo, stamp), repo, stamp, path, text, info, live: isLive(info) && !stopped, stopped, interpreter: info.interpreter }
}

/**
 * Every audit to consider: the session's repository's, and those ~/.specaudit/audits.json lists, each read from its own
 * register, which that index only points to. A listed audit is followed while it is not closed, and the last one
 * written also once it is (as the single beacon was), so that an audit launched elsewhere (a test's throwaway
 * repository) shows without changing folder. An old beacon's repository, or a listed audit whose register has gone, is
 * searched as the session's is.
 */
async function collect($: EngineInterface) {
  const here = await $.session.cwd()
  const own = slash((await run($, ['git', 'rev-parse', '--show-toplevel'], here))?.trim() || here)
  const found: Found[] = []
  const seen = (key: string) => found.some(f => f.key.toLowerCase() === key.toLowerCase())
  const add = async (repo: string, stamp: string, path: string) => {
    if (seen(auditKey(repo, stamp))) return
    const f = await load($, repo, stamp, path)
    if (f) found.push(f)
  }
  for (const r of await registersOf($, own)) await add(own, r.stamp, r.path)
  const entries = await listed($, here, pickAudit(found))
  const last = entries.reduce<Listed | undefined>((a, b) => (!a || (b.updatedAt ?? 0) > (a.updatedAt ?? 0) ? b : a), undefined)
  const searched = new Set([own.toLowerCase()])
  for (const entry of entries) {
    if (entry.state === 'closed' && entry !== last) continue
    const repo = slash(entry.repo)
    if (entry.stamp && seen(auditKey(repo, entry.stamp))) continue
    let path: string | undefined
    for (const p of [entry.register, entry.results && `${slash(entry.results)}/register.md`]) {
      if (p && (await $.fs.exists(p).catch(() => false))) {
        path = p
        break
      }
    }
    if (entry.stamp && path) await add(repo, entry.stamp, path)
    else if (!searched.has(repo.toLowerCase())) {
      searched.add(repo.toLowerCase())
      for (const r of await registersOf($, repo)) await add(repo, r.stamp, r.path)
    }
  }
  return { own, found: uniqueAudits(found) }
}

/** The band's and the pane's list: every live audit, and the one shown, newest first. */
function linesOf(found: Found[], shown: Found): AuditLine[] {
  return found
    .filter(f => f.live || f.key === shown.key)
    .sort((a, b) => b.stamp.localeCompare(a.stamp))
    .map(f => ({
      key: f.key,
      project: baseName(f.repo),
      stamp: f.stamp,
      document: f.info.document,
      isLive: f.live,
      stage: f.stopped ? `Arrêté : ${f.stopped}` : stageOf(f.info),
      state: f.info.state,
      stopped: f.stopped,
      evaluated: f.info.counts.evaluated,
      total: f.info.counts.total,
    }))
}

async function refresh($: EngineInterface) {
  const { own, found } = await collect($)
  const best = pickAudit(found, await read($, selected))
  cwd = best?.repo ?? own
  const project = baseName(cwd)
  if (!best) {
    await update($, snapshot, () => ({ project, isLive: false, stage: 'Aucun audit', updatedAt: Date.now() }))
    return false
  }
  const newest = best
  const text = best.text
  const info = best.info
  const live = best.live
  const snap: Snapshot = {
    project,
    stamp: newest.stamp,
    document: info.document,
    isLive: live,
    stage: best.stopped ? `Arrêté : ${best.stopped}` : stageOf(info),
    stopped: best.stopped,
    state: info.state,
    branch: info.branch,
    scratch: info.scratch,
    launcher: info.launcher,
    inProcess: info.inProcess,
    stopRequested: !!info.scratch && (await $.fs.exists(`${info.scratch}/stop-requested`).catch(() => false)),
    counts: info.counts,
    errors: listErrors(text),
    agent: info.agent,
    agentsDone: info.agentsDone,
    agentsTotal: info.agentsTotal,
    iterations: info.iterations,
    revisions: info.revisions,
    resumes: info.resumes,
    key: best.key,
    audits: linesOf(found, best),
    updatedAt: Date.now(),
  }

  if (info.scratch) {
    const out = await run($, [info.interpreter, '-I', `${$.plugin.root}/hooks/probe.py`, `${info.scratch}/launch`])
    try {
      const probe = out ? (JSON.parse(out) as Probe) : undefined
      if (probe) {
        const win = (w: Probe['session'], limit: number): Window | undefined =>
          w ? { now: w.now, start: w.start, limit, resetsAt: w.resetsAt } : undefined
        snap.session = win(probe.session, info.pauseAt.session)
        snap.week = win(probe.week, info.pauseAt.week)
        snap.turns = probe.turns
        snap.tokens = probe.tokens
        snap.cost = probe.cost || undefined
      }
    } catch {
      // a probe that printed no JSON leaves the usage out
    }
  }

  if (info.base && info.branch) {
    const count = await run($, ['git', 'rev-list', '--count', `${info.base}..${info.branch}`])
    if (count) snap.commits = Number(count.trim())
    if (info.corpus) {
      const added = await run($, ['git', 'diff', '--name-only', '--diff-filter=A', info.base, info.branch, '--', info.corpus])
      if (added !== undefined) snap.guards = added.split('\n').filter(f => /\.py$|\.lean$|\.ts$/.test(f.trim())).length
    }
  }

  if (!live && !best.stopped) {
    const index = indexSection((await readText($, `${slash(cwd)}/SPECAUDITS.md`)) ?? '', newest.stamp)
    snap.result = index['Result']
    // An audit that ended with a fix or a choice left to the person waits on them, not on the audit.
    if (/needs decision|pending/i.test(snap.result ?? '')) snap.stage = 'En attente de ta décision'
    snap.consumption = index['Consumption']
  }

  await update($, snapshot, () => snap)
  return true
}

/** Refreshes; while the repository has no audit, the detail pane closes (the band draws nothing of its own then). */
async function refreshAndShow($: EngineInterface) {
  if (!(await refresh($))) await $.ui.close({ id: PANE }).catch(() => undefined)
}

async function openPane($: EngineInterface) {
  await $.ui.open({ id: PANE, title: `SpecAudit · ${baseName(cwd)}` })
}

/** Shows the audit of `key`, chosen in the band's list or the pane's, until another is chosen or it is no longer found. */
async function choose($: EngineInterface, key: string) {
  await update($, selected, () => key)
  await update($, armed, () => 0)
  await refresh($).catch(() => false)
}

/** One line of the list of audits: the one shown marked, its stage's glyph, its project and document, its progress. */
function auditLabel(a: AuditLine, isShown: boolean, width: number) {
  const text = `${a.project} · ${a.document ?? a.stamp}  ${a.evaluated}/${a.total}`
  return { mark: isShown ? '▸' : ' ', status: stageIcon(a), text: cut(text, Math.max(8, width - 4)) }
}

// The band's controls act on the audit it shows, in its own repository (`cwd`, set by refresh): pause and stop write
// stop-requested in its scratch root, which its session's hooks read (SpecAudit's closing.md, 8.9), then tell the
// session that launched it, which owns what follows; resume asks that session for `/spec-audit:start --resume`.
const CONFIRM_MS = 10000

/** Sends `text` to the session that launched the audit, or submits it here when that is this session. */
async function tellLauncher($: EngineInterface, snap: Snapshot, text: string) {
  if (!snap.launcher) return false
  try {
    if (snap.launcher === (await $.session.id())) {
      void $.prompt.submit({ text })
      return true
    }
    return (await $.session.send({ to: { sessionId: snap.launcher }, text })).isDelivered
  } catch {
    return false
  }
}

const auditName = (snap: Snapshot) => `l'audit SpecAudit ${snap.stamp} (${snap.document ?? '?'}, dépôt ${cwd})`

async function requestStop($: EngineInterface, snap: Snapshot) {
  await $.fs.write(`${snap.scratch}/stop-requested`, '')
  await update($, snapshot, s => (s ? { ...s, stopRequested: true } : s))
}

async function pause($: EngineInterface, snap: Snapshot) {
  await requestStop($, snap)
  const told = await tellLauncher(
    $,
    snap,
    `Pause de ${auditName(snap)} demandée depuis le bloc specaudit-monitor : ${snap.scratch}/stop-requested est posé. ` +
      `Quand le processus de l'audit se termine, laisse l'audit suspendu (8.9, « Suspend »), sans clôture ni question ; ` +
      `/spec-audit:start ${snap.document} --resume le reprendra.`,
  )
  $.ui.toast(
    `Pause demandée : l'audit se suspend après le rapport de l'agent en cours.` +
      (told ? '' : ` Session de lancement ${snap.launcher ?? '?'} injoignable : l'audit restera suspendu.`),
  )
}

async function stop($: EngineInterface, snap: Snapshot) {
  if (Date.now() - (await read($, armed)) > CONFIRM_MS) {
    await update($, armed, () => Date.now())
    $.ui.toast("Appuie encore sur stop dans les 10 s pour arrêter l'audit.")
    return
  }
  await update($, armed, () => 0)
  await requestStop($, snap)
  const told = await tellLauncher(
    $,
    snap,
    `Arrêt de ${auditName(snap)} demandé depuis le bloc specaudit-monitor : ${snap.scratch}/stop-requested est posé. ` +
      `Exécute /spec-audit:stop ${snap.document} (8.9 de closing.md) : attends la fin du processus, fais le point et ` +
      `pose la question « Stop ».`,
  )
  $.ui.toast(
    told
      ? "Arrêt demandé : la session de lancement fera le point et te demandera comment finir l'audit."
      : `Arrêt demandé, l'audit se suspend. Pour décider de la suite : /spec-audit:stop ${snap.document} depuis la session ${snap.launcher ?? '?'}.`,
  )
}

// The start skill's command: `spec-audit:start` from the plugin, `spec-audit-start` copied by hand (docs/installation.md).
const START_COMMANDS = ['spec-audit:start', 'spec-audit-start']

/**
 * Resumes the audit: its launcher does it while it runs; once it has gone, this session does, as
 * `/spec-audit:start <document> --resume` typed here would, and so becomes the audit's launcher. That takes a session
 * opened in the audit's repository (the skill resumes the audit of its own) and the start skill installed in it.
 */
async function resume($: EngineInterface, snap: Snapshot) {
  const args = `${snap.document} --resume`
  if (!snap.stopped) {
    const told = await tellLauncher($, snap, `Reprise de ${auditName(snap)} demandée depuis le bloc specaudit-monitor : exécute /spec-audit:start ${args} dans ${cwd}.`)
    if (told) {
      $.ui.toast("Reprise demandée à la session de lancement de l'audit.")
      return
    }
  }
  const here = await $.session.cwd()
  const root = slash((await run($, ['git', 'rev-parse', '--show-toplevel'], here))?.trim() || here)
  const names = (await $.command.list().catch(() => [])).map(c => c.name)
  const command = START_COMMANDS.find(name => names.includes(name))
  if (!command) {
    $.ui.toast(`Le skill spec-audit n'est pas installé dans cette session : lance /spec-audit:start ${args} depuis une session ouverte dans ${cwd}.`)
    return
  }
  if (root.toLowerCase() !== cwd.toLowerCase()) {
    $.ui.toast(`Cette session est ouverte dans ${baseName(root)}, pas dans le dépôt de l'audit : lance /${command} ${args} depuis une session ouverte dans ${cwd}.`)
    return
  }
  await $.command.run({ command, args })
  $.ui.toast("Reprise lancée dans cette session, qui devient la session de lancement de l'audit.")
}

/** A text cut to `n` cells, an ellipsis in its last one. */
const cut = (text: string, n: number) => (text.length <= n ? text : `${text.slice(0, Math.max(0, n - 1))}…`)

const pct = (x: number) => `${Math.round(x * 100)} %`

/** The usage windows the audit has, each with the share of its margin used and its tone: shown side by side. */
function windowsOf(snap: Snapshot) {
  return [
    snap.session && { name: '5 h', w: snap.session },
    snap.week && { name: 'sem.', w: snap.week },
  ]
    .filter((x): x is { name: string; w: Window } => !!x)
    .map(({ name, w }) => {
      const used = marginUsed(w)
      return { name, used, tone: used >= 0.9 ? 'error' : used >= 0.7 ? 'warning' : 'success' } as const
    })
}

const stageTone = (snap: Snapshot) =>
  snap.stage === 'Terminé' ? 'success' : snap.stage.startsWith('En ') || snap.stage === 'Suspendu' ? 'warning' : undefined

/** The stage as one glyph and its colour, for the band's first line; the stage in words is the pane's. */
function stageIcon(snap: Pick<Snapshot, 'stage' | 'stopped' | 'state' | 'isLive'>): { glyph: string; color?: string } {
  if (snap.stage === 'Terminé') return { glyph: '✔', color: 'success' }
  if (snap.stopped) return { glyph: '⏹' }
  if (snap.stage === 'En attente de ta décision') return { glyph: '?', color: 'warning' }
  if (snap.state?.startsWith('suspended')) return { glyph: '⏸', color: 'warning' }
  if (snap.state?.startsWith('stopping')) return { glyph: '⏹', color: 'warning' }
  return snap.isLive ? { glyph: '●', color: ICON_COLOR } : { glyph: '·' }
}

// A status as an icon, one cell wide on every surface, and its colour; a row's hover card says it in words.
const STATUS_ICON: Record<string, { icon: string; label: string; color?: string }> = {
  DETECTED: { icon: '·', label: 'détectée' },
  CONFIRMED: { icon: '!', label: 'confirmée', color: 'warning' },
  FIXED: { icon: '✔', label: 'corrigée', color: 'success' },
  REFUTED: { icon: '✘', label: 'réfutée' },
  RESOLVED: { icon: '↳', label: 'résolue par sa cause', color: 'success' },
  UNDECIDED: { icon: '?', label: 'indécise', color: 'warning' },
  BLOCKED: { icon: '⊘', label: 'bloquée', color: 'warning' },
  ESCALATED: { icon: '⇡', label: 'remontée', color: 'warning' },
  RECURRENCE: { icon: '↻', label: 'récidive', color: 'error' },
}

/** A register status (`FIXED (r3)`, `BLOCKED (by F-1-1)`): its icon, and what follows it as a note (`r3`, `par F-1-1`). */
function statusOf(status: string) {
  const word = /^[A-Z]+/.exec(status)?.[0] ?? status
  const known = STATUS_ICON[word]
  const note = status
    .slice(word.length)
    .trim()
    .replace(/^\((.*)\)$/, '$1')
    .replace(/^[—–-]\s*/, '')
    .replace(/^by /, 'par ')
  return { word, icon: known?.icon ?? '·', color: known?.color, note: known ? note : status }
}

/** The hover card of one error, in Markdown: its status in words, then each field the register gives. */
function tipOf(err: ErrorRow): string {
  const { word, note } = statusOf(err.status)
  const status = `${STATUS_ICON[word]?.icon ?? ''} *${STATUS_ICON[word]?.label ?? word}*${note ? ` · ${note}` : ''}`
  const fields: [string, string | undefined][] = [
    ['Gravité', err.severity],
    ['Type', err.type],
    ['Causes', err.causes],
    ['Emplacement', err.location],
    ['Preuve', err.evidence],
    ['Garde-fous', err.guards],
    ['Correction', err.fix],
  ]
  return [
    `**${err.id} — ${err.title}**`,
    '',
    status,
    '',
    ...fields.filter(([, v]) => v).map(([k, v]) => `- **${k}** : ${v}`),
  ].join('\n')
}

/** The consumption as label and value lines: the index's row once the audit ended, the stream's figures meanwhile. */
function consumptionLines(snap: Snapshot): [string, string][] {
  if (snap.consumption) {
    return snap.consumption.split(/,\s*/).map((part): [string, string] => {
      if (/tokens/.test(part)) return ['Tokens', part.replace(/\s*tokens/, '')]
      if (/^\$|USD/.test(part)) return ['Coût', part]
      const week = /^(\d+(?:\.\d+)?) points? of the week window/.exec(part)
      if (week) return ['Part semaine', `${week[1]} point${week[1] === '1' ? '' : 's'}`]
      const session = /^(\d+(?:\.\d+)?) points? of the session window/.exec(part)
      if (session) return ['Part 5 h', `${session[1]} point${session[1] === '1' ? '' : 's'}`]
      return ['', part]
    })
  }
  const out: [string, string][] = []
  if (snap.tokens !== undefined) out.push(['Tokens', `≈ ${compact(snap.tokens)}`])
  if (snap.cost) out.push(['Coût', `$${snap.cost.toFixed(2)} (exécutions terminées)`])
  return out
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    cwd = e.cwd
    await $.command.register({ name: 'specaudit-pane', description: 'Show the detail of the SpecAudit audit of this project' })
    await refreshAndShow($)

    let n = 0
    $.clock.every(TICK_MS, async () => {
      n += 1
      const snap = await read($, snapshot)
      if (snap?.isLive) await update($, tick, t => t + 1)
      if (n % (snap?.isLive ? LIVE_EVERY : IDLE_EVERY) === 0) await refreshAndShow($)
    })

    return started
  })

  on('command.run', { command: 'specaudit-pane' }, async $ => {
    if (!(await refresh($))) return { text: `No SpecAudit audit in ${baseName(cwd)}: no pane to show.` }
    await openPane($)

    return { text: 'SpecAudit pane opened.' }
  })

  // The compact widget, above the prompt: what the audit is at, its progress and its usage margin, one press from the
  // detail. Nothing of its own while the repository has no audit, or while a survey holds the band.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const snap = await read($, snapshot)
    if (e.props.hasSurvey || !snap?.stamp) return next(e)

    const els = $.ui.resolve(e)
    const { Box, Text, Button } = els
    const icon =
      'Svg' in els ? <els.Svg source={ICON} alt="SpecAudit" width={14} height={14} /> : <Text color={ICON_COLOR}>∎</Text>
    const t = await read($, tick)
    const c = snap.counts
    const windows = windowsOf(snap)
    const { canPause, canStop, canResume } = controlsOf(snap)
    const isArmed = Date.now() - (await read($, armed)) <= CONFIRM_MS
    const isSuspended = !!snap.state?.startsWith('suspended')
    const status = stageIcon(snap)
    const alerts = limitAlerts(snap)
    const list = snap.audits ?? []
    const columns = e.props.bodyColumns ?? 80
    // The title and the progress take two rows, each alert one; the list takes what is left, one row at least.
    const room = Math.max(1, (e.props.maxRows ?? 6) - 2 - alerts.length)
    // A control is a glyph alone, padded to twice its width: an easier target. Only the controls the audit's state
    // allows are drawn (controlsOf): pause and stop while it runs, resume once it is suspended, none once it has
    // stopped or ended. Its label names it for a screen reader.
    const control = (key: string, glyph: string, label: string, act: () => unknown, color?: string) => (
      <Button key={key} label={label} plain onPress={() => void act()}>
        <Text color={color}>{` ${glyph} `}</Text>
      </Button>
    )

    return (
      <Box flexDirection="column">
        <Box flexDirection="row">
          <Box flexDirection="row" gap={1} flexGrow={1} flexShrink={1} minWidth={0}>
            {icon}
            <Text bold>SpecAudit</Text>
            <Text wrap="truncate-end">{snap.document ?? snap.project}</Text>
            {/* The stage as its icon alone: the limit alerts below say in words what a pause is about. */}
            <Text key="stage" color={status.color} dimColor={!status.color}>
              {status.glyph}
            </Text>
          </Box>
          {/* The detail, top right, as a maximize glyph: the pane is the band at full size. */}
          <Box flexShrink={0}>{control('detail', '⤢', 'Détails', () => openPane($))}</Box>
        </Box>
        {/* With more than one live audit, one line each, a button that shows it here (▸ the one shown), in the rows the
            band has left; the pane lists any that do not fit. */}
        {list.length > 1 &&
          list.slice(0, room).map((a, i) => {
            const overflow = i === room - 1 && list.length > room
            const { mark, status: s, text } = auditLabel(a, a.key === snap.key, columns)
            return overflow ? (
              <Button key="pick-more" label="Tous les audits" plain onPress={() => void openPane($)}>
                <Text dimColor>{`  … ${list.length - room + 1} autres audits en cours ⤢`}</Text>
              </Button>
            ) : (
              <Button key={`pick-${a.stamp}`} label={`Afficher ${a.project} · ${a.document ?? a.stamp}`} plain onPress={() => void choose($, a.key)}>
                <Text color={a.key === snap.key ? ICON_COLOR : undefined}>{mark}</Text>
                <Text color={s.color} dimColor={!s.color}>{` ${s.glyph} `}</Text>
                <Text>{text}</Text>
              </Button>
            )
          })}
        {/* The usage windows near their pause threshold, one line each, between the title and the progress. */}
        {alerts.map(a => (
          <Text key={`limit-${a.name}`} color={a.tone} wrap="truncate-end">
            {`⚠ Limite ${a.name} : ${pct(a.used)} de la marge utilisée (compte à ${pct(a.now)}, pause à ${pct(a.limit)})`}
          </Text>
        ))}
        <Box flexDirection="row">
          <Box flexGrow={1} flexShrink={1} minWidth={0}>
            {snap.isLive ? (
              // No bar in the band: a spinner says the audit is working (⏸ once it is suspended), the figures say how far.
              <Text wrap="truncate-end">
                <Text color={isSuspended ? 'warning' : ICON_COLOR}>{isSuspended ? '⏸' : SPINNER[t % SPINNER.length]}</Text>
                <Text dimColor> Avancement </Text>
                {c ? `${c.evaluated}/${c.total}` : '…'}
                {windows.length > 0 && <Text dimColor>   Marge</Text>}
                {windows.map((w, i) => (
                  <Text key={`margin-${w.name}`}>
                    <Text dimColor>{`${i > 0 ? ' ·' : ''} ${w.name} `}</Text>
                    <Text color={w.tone}>{pct(w.used)}</Text>
                  </Text>
                ))}
              </Text>
            ) : (
              <Text dimColor wrap="truncate-end">
                {c ? `${c.confirmed} erreurs confirmées · ${c.fixed} corrigées` : ''}
                {snap.guards !== undefined ? ` · ${snap.guards} garde-fous` : ''}
                {snap.result ? ` · ${snap.result}` : ''}
              </Text>
            )}
          </Box>
          <Box flexDirection="row" flexShrink={0}>
            {canPause && control('pause', '⏸', 'Mettre en pause', () => pause($, snap))}
            {canStop && control('stop', '⏹', isArmed ? "Confirmer l'arrêt" : 'Arrêter', () => stop($, snap), isArmed ? 'error' : undefined)}
            {canResume && control('resume', '▶', 'Reprendre', () => resume($, snap))}
          </Box>
        </Box>
      </Box>
    )
  })

  // The detail, in a pane the band's button or /specaudit-pane opens: one figure per line, by section, and the errors
  // and usage windows as tables.
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text, Button, Markdown } = els
    const icon =
      'Svg' in els ? <els.Svg source={ICON} alt="SpecAudit" width={14} height={14} /> : <Text color={ICON_COLOR}>∎</Text>
    const snap = await read($, snapshot)
    const columns = e.props.bodyColumns ?? 60
    const width = Math.max(8, Math.min(30, columns - 24))

    if (!snap || !snap.stamp) {
      return (
        <Box flexDirection="column">
          <Box flexDirection="row" gap={1}>
            {icon}
            <Text bold>SpecAudit · {snap?.project ?? baseName(cwd)}</Text>
          </Box>
          <Text dimColor>Aucun audit dans ce projet. /spec-audit:start en lance un.</Text>
        </Box>
      )
    }

    const c = snap.counts
    const LABEL = 16
    const line = (label: string, value: string | number | undefined, color?: string) =>
      value === undefined || value === '' ? undefined : (
        <Box flexDirection="row">
          <Box width={LABEL} flexShrink={0}>
            <Text dimColor>{label}</Text>
          </Box>
          <Text color={color} wrap="truncate-end">
            {String(value)}
          </Text>
        </Box>
      )
    // A section: its title, then its rows; a collapsible one starts folded, its title a button that unfolds it. An
    // accordion: unfolding one folds the others; which one is open is remembered for the session.
    const shown = await read($, unfolded)
    const section = (title: string, isCollapsible: boolean, ...rows: unknown[]) => {
      const isClosed = isCollapsible && !shown.includes(title)
      return (
        <Box flexDirection="column" marginTop={1}>
          {isCollapsible ? (
            <Button
              key={`fold-${title}`}
              plain
              onPress={() => update($, unfolded, list => (list.includes(title) ? [] : [title]))}
            >
              {isClosed ? '▸ ' : '▾ '}
              <Text bold>{title}</Text>
            </Button>
          ) : (
            <Text bold>{title}</Text>
          )}
          {!isClosed && rows}
        </Box>
      )
    }
    // A table: a width per column, `undefined` for the one that takes the rest; the header dim. `tone` colours one column.
    // One tip open at most: unfolding a row folds the one that was open.
    // A row with a `tip` has its first cell as a button that unfolds the tip, in Markdown, under the row: in the flow,
    // so it covers nothing (a surface gives a pane no opaque background a card could sit on).
    // The tip is as wide as the pane, less its indent: unbounded, it took its longest line's width and was clipped.
    const open = await read($, opened)
    const table = (
      widths: (number | undefined)[],
      header: string[],
      rows: { cells: string[]; color?: string; tip?: string }[],
      tone?: number,
    ) => {
      // The flexible column's width: what the fixed ones leave of the pane.
      const rest = Math.max(8, columns - widths.reduce<number>((sum, w) => sum + (w ?? 0), 0))
      return (
      <Box flexDirection="column">
        {[{ cells: header, isHeader: true }, ...rows].map((r, i) => {
          const id = r.cells[0]
          const tip = 'tip' in r ? r.tip : undefined
          const isOpen = !!tip && open.includes(id)
          return (
            <Box key={`r${i}-${id}`} flexDirection="column">
              <Box flexDirection="row">
                {r.cells.map((cell, j) => (
                  <Box
                    key={`c${j}`}
                    width={widths[j]}
                    flexGrow={widths[j] === undefined ? 1 : 0}
                    flexShrink={widths[j] === undefined ? 1 : 0}
                    minWidth={0}
                    paddingRight={1}
                  >
                    {tip ? (
                      // Every cell of a row with a tip is a button on the same toggle, so the whole row is one target;
                      // its text is cut to the cell first, since a button whose label does not fit draws none of it.
                      <Button
                        key={j === 0 ? `tip-${id}` : `tip-${id}-${j}`}
                        plain
                        onPress={() => update($, opened, list => (list.includes(id) ? [] : [id]))}
                      >
                        {j === 0 ? (isOpen ? '▾ ' : '▸ ') : ''}
                        <Text color={j === tone ? (r as { color?: string }).color : undefined}>
                          {cut(cell, (widths[j] ?? rest) - 1 - (j === 0 ? 2 : 0))}
                        </Text>
                      </Button>
                    ) : (
                      <Text
                        dimColor={'isHeader' in r}
                        color={'isHeader' in r || j !== tone ? undefined : (r as { color?: string }).color}
                        wrap="truncate-end"
                      >
                        {cell}
                      </Text>
                    )}
                  </Box>
                ))}
              </Box>
              {isOpen && (
                <Box
                  width={Math.max(20, columns - 2)}
                  flexShrink={0}
                  marginLeft={2}
                  marginBottom={1}
                  paddingX={1}
                  borderStyle="single"
                  borderColor="subtle"
                >
                  <Markdown text={tip} />
                </Box>
              )}
            </Box>
          )
        })}
      </Box>
      )
    }

    const errorRows = (snap.errors ?? []).map(err => {
      const { icon, color, note } = statusOf(err.status)
      return { cells: [err.id, icon, err.title, note], color, tip: tipOf(err) }
    })
    const usageRows = [
      snap.session && { name: '5 h', w: snap.session },
      snap.week && { name: 'Semaine', w: snap.week },
    ]
      .filter((x): x is { name: string; w: Window } => !!x)
      .map(({ name, w }) => ({ cells: [name, pct(w.start), pct(w.now), pct(w.limit), pct(marginUsed(w))] }))

    return (
      <Box flexDirection="column">
        <Box flexDirection="row" gap={1}>
          {icon}
          <Text bold wrap="truncate-end">
            SpecAudit · {snap.project} · {snap.document ?? '?'}
          </Text>
        </Box>
        {line('Stade', snap.stage, stageTone(snap))}
        {line('Résultat', snap.result)}
        {line('Branche', snap.branch)}

        {/* Every live audit, when there is more than one: each a button that shows it, here and in the band. */}
        {(snap.audits ?? []).length > 1 &&
          section(
            'Audits en cours',
            false,
            ...(snap.audits ?? []).map(a => {
              const { mark, status: s, text } = auditLabel(a, a.key === snap.key, columns)
              return (
                <Button key={`pane-pick-${a.stamp}`} label={`Afficher ${a.project} · ${a.document ?? a.stamp}`} plain onPress={() => void choose($, a.key)}>
                  <Text color={a.key === snap.key ? ICON_COLOR : undefined}>{mark}</Text>
                  <Text color={s.color} dimColor={!s.color}>{` ${s.glyph} `}</Text>
                  <Text bold={a.key === snap.key}>{text}</Text>
                </Button>
              )
            }),
          )}

        {section(
          'Consommation',
          false,
          ...consumptionLines(snap).map(([label, value]) => line(label, value)),
          line('Tours', snap.turns),
          snap.isLive && usageRows.length > 0 && (
            <Box marginTop={1}>
              {table([LABEL, 9, 9, 9, undefined], ['Fenêtre', 'Départ', 'Actuel', 'Pause', 'Marge utilisée'], usageRows)}
            </Box>
          ),
        )}

        {snap.isLive &&
          section(
            'Avancement',
            true,
            line('Erreurs évaluées', c ? `${bar(c.total > 0 ? c.evaluated / c.total : 0, width)} ${c.evaluated}/${c.total}` : '…'),
            ...[
              snap.session && { name: 'Marge 5 h', w: snap.session },
              snap.week && { name: 'Marge semaine', w: snap.week },
            ]
              .filter((x): x is { name: string; w: Window } => !!x)
              .map(({ name, w }) => {
                const used = marginUsed(w)
                return line(name, `${bar(used, width)} ${pct(used)}`, used >= 0.9 ? 'error' : used >= 0.7 ? 'warning' : 'success')
              }),
            line('Agent en cours', snap.agent),
          )}

        {c &&
          section(
            'Erreurs',
            true,
            line('Détectées', c.total),
            line('Évaluées', c.evaluated),
            line('Confirmées', c.confirmed),
            line('Corrigées', c.fixed, c.fixed > 0 ? 'success' : undefined),
            line('Réfutées', c.refuted),
            c.resolved > 0 ? line('Résolues', c.resolved) : undefined,
            c.undecided > 0 ? line('Indécises', c.undecided, 'warning') : undefined,
            c.blocked > 0 ? line('Bloquées', c.blocked, 'warning') : undefined,
            errorRows.length > 0 && (
              <Box marginTop={1}>{table([LABEL, 3, undefined, 18], ['Id', '', 'Énoncé', 'Notes'], errorRows, 1)}</Box>
            ),
          )}

        {section(
          'Preuves',
          true,
          line('Garde-fous', snap.guards !== undefined ? `${snap.guards} fichiers ajoutés au corpus` : undefined),
          line('Contre-exemples', c ? `${c.confirmed} exécutés (un par erreur confirmée)` : undefined),
        )}

        {section(
          'Technique',
          true,
          line('Agents', snap.agentsTotal ? `${snap.agentsDone}/${snap.agentsTotal} terminés` : undefined),
          line('Commits', snap.commits),
          line('Révisions', snap.revisions),
          line('Passes', snap.iterations),
          snap.resumes ? line('Reprises', snap.resumes) : undefined,
        )}
      </Box>
    )
  })
}
