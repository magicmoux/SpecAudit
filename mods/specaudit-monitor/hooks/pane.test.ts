import { expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'

import type { Snapshot } from '../types'

const ALL_SECTIONS = ['Avancement', 'Erreurs', 'Preuves', 'Technique']

// The kit's $ has no state noun: a hook beneath the plugin answers its reads of the snapshot, and of the unfolded
// sections until the plugin writes them (every section unless told otherwise, so that tests read their rows).
function seed(on: On, snapshot: Snapshot, unfolded: string[] = ALL_SECTIONS) {
  on('state.get', async ($, e, next) => {
    if (e.plugin !== 'specaudit-monitor') return next(e)
    if (e.key === 'snapshot') return { value: { value: snapshot, version: 1 } }
    const held = await next(e)
    return e.key === 'unfolded' && held.value?.value === undefined ? { value: { value: unfolded, version: 0 } } : held
  })
}

const PANE = {
  component: 'Pane' as const,
  requestId: 'specaudit',
  props: {
    title: 'SpecAudit · demo',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  } as never,
}

const BAND = {
  component: 'AbovePrompt' as const,
  props: { hasSurvey: false, isWorking: false, maxRows: 6, bodyColumns: 100 } as never,
}

const LIVE: Snapshot = {
  project: 'demo',
  stamp: '20261015_175354',
  document: 'selection.md',
  isLive: true,
  stage: 'Agent : adjudicator F-1-2',
  branch: 'audit/20261015_175354',
  counts: { total: 6, evaluated: 3, confirmed: 2, fixed: 1, refuted: 1, resolved: 0, undecided: 0, blocked: 1 },
  agentsDone: 4,
  agentsTotal: 5,
  session: { start: 0.02, now: 0.04, limit: 0.07 },
  week: { start: 0.22, now: 0.22, limit: 0.25 },
  turns: 42,
  tokens: 1_200_000,
  commits: 3,
  guards: 4,
  updatedAt: 0,
}

const DONE: Snapshot = {
  ...LIVE,
  isLive: false,
  stage: 'En attente de ta décision',
  counts: { total: 6, evaluated: 6, confirmed: 6, fixed: 5, refuted: 0, resolved: 0, undecided: 0, blocked: 0 },
  result: 'FINISHED — Partial, needs decision',
  consumption: '6.38 M tokens, $2.10, 0 points of the week window',
  iterations: 1,
  revisions: 5,
  errors: [
    { id: 'F-1-1', title: 'Lemma 3 ignores n < k', status: 'FIXED (r3)', severity: 'major' },
    { id: 'F-1-6', title: 'Abstract and Conclusion claim exactly k elements', status: 'CONFIRMED' },
  ],
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`band: a live audit's progress and margin (${surface})`, async ($, on) => {
    seed(on, LIVE)
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...BAND })
    expect(await ui.find({ type: 'Text', text: /Agent : adjudicator F-1-2/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /3\/6/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Marge 5 h/ })).toBeDefined()
    expect(await ui.find({ key: 'detail' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /[█░▏▎▍▌▋▊▉]/ })).toBeUndefined()
    await ui.unmount()
  })

  test(`band: pause and stop while it runs, resume greyed (${surface})`, async ($, on) => {
    seed(on, { ...LIVE, state: 'running', scratch: 'C:/x-scratch', launcher: '705774c1', inProcess: true })
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...BAND })
    expect(await ui.find({ type: 'Button', key: 'pause' })).toBeDefined()
    expect(await ui.find({ type: 'Button', key: 'stop' })).toBeDefined()
    expect(await ui.find({ type: 'Button', key: 'resume' })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /▶ reprendre/ })).toBeDefined()
    await ui.press({ key: 'stop' })
    expect(await ui.find({ type: 'Button', key: 'stop', text: /confirmer/ })).toBeDefined()
    await ui.unmount()
  })

  test(`band: a suspended audit offers resume alone (${surface})`, async ($, on) => {
    seed(on, { ...LIVE, state: 'suspended (stopped on request)', stage: 'Suspendu', scratch: 'C:/x-scratch', launcher: '705774c1', inProcess: true })
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...BAND })
    expect(await ui.find({ type: 'Button', key: 'resume' })).toBeDefined()
    expect(await ui.find({ type: 'Button', key: 'pause' })).toBeUndefined()
    expect(await ui.find({ type: 'Button', key: 'stop' })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /⏸ pause/ })).toBeDefined()
    await ui.unmount()
  })

  test(`band: a finished audit waiting on a decision (${surface})`, async ($, on) => {
    seed(on, DONE)
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...BAND })
    expect(await ui.find({ type: 'Text', text: /En attente de ta décision/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /6 erreurs confirmées · 5 corrigées · 4 garde-fous/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Marge/ })).toBeUndefined()
    await ui.unmount()
  })

  test(`pane: the detail of a finished audit (${surface})`, async ($, on) => {
    seed(on, DONE)
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...PANE })
    expect(await ui.find({ type: 'Text', text: /FINISHED/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Corrigées$/ })).toBeDefined()
    expect(await ui.find({ key: 'tip-F-1-1' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^✔$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^!$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^r3$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Notes$/ })).toBeDefined()
    expect(await ui.find({ type: 'Markdown' })).toBeUndefined()
    await ui.press({ key: 'tip-F-1-1' })
    expect(await ui.find({ type: 'Markdown', text: /F-1-1 — Lemma 3 ignores n < k[\s\S]*Gravité\*\* : major/ })).toBeDefined()
    await ui.press({ key: 'tip-F-1-1' })
    expect(await ui.find({ type: 'Markdown' })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /^✔ corrigée/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /^Lemma 3 ignores n < k$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^6\.38 M$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^\$2\.10$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Part semaine$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Technique/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /audit\/20261015_175354/ })).toBeDefined()
    await ui.unmount()
  })

  test(`pane: a live audit with its bars and usage (${surface})`, async ($, on) => {
    seed(on, LIVE)
    const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface, ...PANE })
    expect(await ui.find({ type: 'Text', text: /Avancement/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Marge 5 h$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Fenêtre$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Semaine$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Tours/ })).toBeDefined()
    await ui.unmount()
  })
}

// What the engine draws in the band when no plugin does: nothing here.
const bottom = (on: On) =>
  on('ui.render', async ($, e) => {
    const { Box } = $.ui.resolve(e)
    return h(Box, { key: 'engine' }) as never
  })

test('band: nothing of its own without an audit', async ($, on) => {
  bottom(on)
  seed(on, { project: 'demo', isLive: false, stage: 'Aucun audit', updatedAt: 0 })
  const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface: 'desktop', ...BAND })
  expect(await ui.find({ type: 'Text', text: /SpecAudit/ })).toBeUndefined()
  await ui.unmount()
})

test('band: yields to a survey', async ($, on) => {
  bottom(on)
  seed(on, LIVE)
  const ui = await $.ui.mount({
    plugin: 'specaudit-monitor',
    surface: 'desktop',
    ...BAND,
    props: { hasSurvey: true, isWorking: false, maxRows: 6, bodyColumns: 100 } as never,
  })
  expect(await ui.find({ type: 'Text', text: /SpecAudit/ })).toBeUndefined()
  await ui.unmount()
})

test('pane: consumption first and open, the other sections folded until unfolded', async ($, on) => {
  seed(on, DONE, [])
  const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface: 'desktop', ...PANE })
  const titles = (await ui.findAll({ type: 'Text', text: /^(Consommation|Erreurs|Preuves|Technique)$/ })).map(t => t.text)
  expect(titles).toEqual(['Consommation', 'Erreurs', 'Preuves', 'Technique'])
  expect(await ui.find({ key: 'fold-Consommation' })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /^Part semaine$/ })).toBeDefined()
  expect(await ui.find({ key: 'tip-F-1-1' })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /^Garde-fous$/ })).toBeUndefined()
  await ui.press({ key: 'fold-Erreurs' })
  expect(await ui.find({ key: 'tip-F-1-1' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^Garde-fous$/ })).toBeUndefined()
  await ui.press({ key: 'fold-Preuves' })
  expect(await ui.find({ type: 'Text', text: /^Garde-fous$/ })).toBeDefined()
  expect(await ui.find({ key: 'tip-F-1-1' })).toBeUndefined()
  await ui.press({ key: 'fold-Preuves' })
  expect(await ui.find({ type: 'Text', text: /^Garde-fous$/ })).toBeUndefined()
  await ui.unmount()
})

test('pane: the whole error row unfolds its detail', async ($, on) => {
  seed(on, DONE)
  const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface: 'desktop', ...PANE })
  await ui.press({ key: 'tip-F-1-1-2' })
  expect(await ui.find({ type: 'Markdown', text: /F-1-1 — Lemma 3/ })).toBeDefined()
  await ui.press({ key: 'tip-F-1-1-3' })
  expect(await ui.find({ type: 'Markdown' })).toBeUndefined()
  await ui.unmount()
})

test('pane: one error detail open at a time', async ($, on) => {
  seed(on, DONE)
  const ui = await $.ui.mount({ plugin: 'specaudit-monitor', surface: 'desktop', ...PANE })
  await ui.press({ key: 'tip-F-1-1' })
  expect(await ui.find({ type: 'Markdown', text: /F-1-1 —/ })).toBeDefined()
  await ui.press({ key: 'tip-F-1-6' })
  expect(await ui.find({ type: 'Markdown', text: /F-1-6 —/ })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /F-1-1 —/ })).toBeUndefined()
  expect((await ui.findAll({ type: 'Markdown' })).length).toBe(1)
  await ui.unmount()
})
