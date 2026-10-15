import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { ErrorRow, Snapshot, Window } from '../types'
import {
  auditWorktrees,
  bar,
  compact,
  controlsOf,
  indexSection,
  isLive,
  listErrors,
  marginUsed,
  parseRegister,
  stageOf,
} from './parse'

const PANE = 'specaudit'
const snapshot = atom({ plugin: 'specaudit-monitor', key: 'snapshot' } as const, null)
const tick = atom({ plugin: 'specaudit-monitor', key: 'tick' } as const, 0)
const unfolded = atom({ plugin: 'specaudit-monitor', key: 'unfolded' } as const, [])
const opened = atom({ plugin: 'specaudit-monitor', key: 'opened' } as const, [])
const armed = atom({ plugin: 'specaudit-monitor', key: 'armed' } as const, 0)

// One tick a second turns the band's spinner, and every 5 s alternates the usage window it shows; a live audit is
// read every 10 s, otherwise every 20 s, so that an
// audit launched meanwhile, or a change of folder, shows soon.
const TICK_MS = 1000
const LIVE_EVERY = 10
const IDLE_EVERY = 20
const ALTERNATE_EVERY = 5
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

// The root of the repository shown: the session's (its cwd's top level), or the one the beacon names when its audit
// is the livelier or the newer.
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

/** The newest audit of a repository: its live register in the worktree when there is one, else its results folder. */
async function newestRegister($: EngineInterface, repo: string) {
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
  for (const entry of await $.fs.list(repo).catch(() => [])) {
    const stamp = /^SpecAudit-(\d{8}_\d{6})$/.exec(entry.name)?.[1]
    const path = `${slash(repo)}/${entry.name}/register.md`
    if (stamp && !found.some(f => f.stamp === stamp) && (await $.fs.exists(path))) found.push({ stamp, path })
  }
  return found.sort((a, b) => b.stamp.localeCompare(a.stamp))[0]
}

// The interpreter that ran beacon.py, found once: `python3` is a stub on Windows, and trying it again at every poll
// would change nothing. When none runs, the search waits for a day, or for a new audit of the session's repository,
// whose register names an interpreter that works.
const RETRY_MS = 24 * 3600 * 1000
let python: string | undefined
let failed: { at: number; stamp?: string } | undefined

/** The repository the beacon names (index.py writes it at each write of an index), if any. */
async function beaconRepo($: EngineInterface, dir: string, audit?: { stamp: string; interpreter?: string }) {
  if (failed && failed.stamp === audit?.stamp && Date.now() - failed.at < RETRY_MS) return undefined
  const candidates = python ? [python] : [...new Set([audit?.interpreter, 'python3', 'python'].filter((c): c is string => !!c))]
  for (const candidate of candidates) {
    const out = await run($, [candidate, '-I', `${$.plugin.root}/hooks/beacon.py`], dir)
    if (out === undefined) continue
    python = candidate
    failed = undefined
    try {
      const repo = (JSON.parse(out) as { repo?: unknown }).repo
      return typeof repo === 'string' && repo ? slash(repo) : undefined
    } catch {
      return undefined
    }
  }
  python = undefined
  failed = { at: Date.now(), stamp: audit?.stamp }
  return undefined
}

type Found = { repo: string; stamp: string; path: string; text: string; live: boolean; interpreter?: string }

async function audit($: EngineInterface, repo: string): Promise<Found | undefined> {
  const newest = await newestRegister($, repo)
  if (!newest) return undefined
  const text = (await readText($, newest.path)) ?? ''
  const info = parseRegister(text)
  return { repo, ...newest, text, live: isLive(info), interpreter: info.interpreter }
}

/**
 * The audit to show: the newest of the session's repository and of the one the beacon names, a live one before one that
 * has ended, so that an audit launched elsewhere (a test's throwaway repository) shows without changing folder.
 */
async function pick($: EngineInterface) {
  const here = await $.session.cwd()
  const own = slash((await run($, ['git', 'rev-parse', '--show-toplevel'], here))?.trim() || here)
  let best = await audit($, own)
  const other = await beaconRepo($, here, best)
  if (other && other.toLowerCase() !== own.toLowerCase()) {
    const found = await audit($, other)
    if (found && (!best || (found.live && !best.live) || (found.live === best.live && found.stamp > best.stamp))) best = found
  }
  return { own, best }
}

async function refresh($: EngineInterface) {
  const { own, best } = await pick($)
  cwd = best?.repo ?? own
  const project = baseName(cwd)
  if (!best) {
    await update($, snapshot, () => ({ project, isLive: false, stage: 'Aucun audit', updatedAt: Date.now() }))
    return false
  }
  const newest = best
  const text = best.text
  const info = parseRegister(text)
  const live = best.live
  const snap: Snapshot = {
    project,
    stamp: newest.stamp,
    document: info.document,
    isLive: live,
    stage: stageOf(info),
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

  if (!live) {
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

async function resume($: EngineInterface, snap: Snapshot) {
  const command = `/spec-audit:start ${snap.document} --resume`
  const told = await tellLauncher($, snap, `Reprise de ${auditName(snap)} demandée depuis le bloc specaudit-monitor : exécute ${command} dans ${cwd}.`)
  $.ui.toast(told ? "Reprise demandée à la session de lancement de l'audit." : `Session de lancement injoignable : lance ${command} dans ${cwd}.`)
}

/** A text cut to `n` cells, an ellipsis in its last one. */
const cut = (text: string, n: number) => (text.length <= n ? text : `${text.slice(0, Math.max(0, n - 1))}…`)

const pct = (x: number) => `${Math.round(x * 100)} %`

/** The usage windows the audit has, and the one shown at this tick: they alternate every 5 s. */
function windowsOf(snap: Snapshot, t: number) {
  const windows = [
    snap.session && { name: '5 h', w: snap.session },
    snap.week && { name: 'sem.', w: snap.week },
  ].filter((x): x is { name: string; w: Window } => !!x)
  const shown = windows.length > 0 ? windows[Math.floor(t / ALTERNATE_EVERY) % windows.length] : undefined
  const used = shown ? marginUsed(shown.w) : 0
  const tone = used >= 0.9 ? 'error' : used >= 0.7 ? 'warning' : 'success'
  return { windows, shown, used, tone } as const
}

const stageTone = (snap: Snapshot) =>
  snap.stage === 'Terminé' ? 'success' : snap.stage.startsWith('En ') || snap.stage === 'Suspendu' ? 'warning' : undefined

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
    const { shown, used, tone } = windowsOf(snap, t)
    const { canPause, canStop, canResume } = controlsOf(snap)
    const isArmed = Date.now() - (await read($, armed)) <= CONFIRM_MS
    // A control that cannot act now is drawn greyed, as text: no Button takes a disabled state.
    const control = (key: string, label: string, isActive: boolean, act: () => Promise<void>) =>
      isActive ? (
        <Button key={key} plain onPress={() => void act()}>
          {label}
        </Button>
      ) : (
        <Text key={key} dimColor>
          {label}
        </Text>
      )

    return (
      <Box flexDirection="column">
        <Box flexDirection="row" gap={1}>
          {icon}
          <Text bold wrap="truncate-end">
            SpecAudit · {snap.document ?? snap.project}
          </Text>
          <Text color={stageTone(snap)} dimColor={!stageTone(snap)} wrap="truncate-end">
            {snap.stage}
          </Text>
          <Button key="detail" plain dimColor onPress={() => openPane($)}>
            détails ▸
          </Button>
        </Box>
        {snap.isLive && (
          <Box flexDirection="row" gap={2}>
            {control('pause', '⏸ pause', canPause, () => pause($, snap))}
            {control('stop', isArmed && canStop ? '⏹ confirmer ?' : '⏹ stop', canStop, () => stop($, snap))}
            {control('resume', '▶ reprendre', canResume, () => resume($, snap))}
            {snap.stopRequested && !snap.state?.startsWith('suspended') && <Text dimColor>arrêt demandé…</Text>}
          </Box>
        )}
        {snap.isLive ? (
          // No bar in the band: a spinner says the audit is working (⏸ once it is suspended), the figures say how far.
          <Text>
            <Text color={snap.state?.startsWith('suspended') ? 'warning' : ICON_COLOR}>
              {snap.state?.startsWith('suspended') ? '⏸' : SPINNER[t % SPINNER.length]}
            </Text>
            <Text dimColor> Avancement </Text>
            {c ? `${c.evaluated}/${c.total}` : '…'}
            {shown && (
              <Text>
                <Text dimColor>{`   Marge ${shown.name} `}</Text>
                <Text color={tone}>{pct(used)}</Text>
              </Text>
            )}
          </Text>
        ) : (
          <Text dimColor>
            {c ? `${c.confirmed} erreurs confirmées · ${c.fixed} corrigées` : ''}
            {snap.guards !== undefined ? ` · ${snap.guards} garde-fous` : ''}
            {snap.result ? ` · ${snap.result}` : ''}
          </Text>
        )}
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
