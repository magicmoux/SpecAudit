export type Counts = {
  total: number
  evaluated: number
  confirmed: number
  fixed: number
  refuted: number
  resolved: number
  undecided: number
  blocked: number
}

/** One error of the register: what the table shows, and what its hover card adds, each field cut to a few lines. */
export type ErrorRow = {
  id: string
  title: string
  status: string
  type?: string
  severity?: string
  causes?: string
  location?: string
  evidence?: string
  guards?: string
  fix?: string
}

/** One usage window: utilization now and at launch (0..1), and the pause threshold (0..1). */
export type Window = { now: number; start: number; limit: number; resetsAt?: number }

export type Snapshot = {
  project: string
  stamp?: string
  document?: string
  /** True while the audit's session is not closed. */
  isLive: boolean
  stage: string
  state?: string
  branch?: string
  /** The audit's scratch root, where the band's buttons write stop-requested. */
  scratch?: string
  /** The id of the session that launched the audit, which decides how a stop ends. */
  launcher?: string
  /** True when the audit runs in a process of its own: only then can the band pause or stop it. */
  inProcess?: boolean
  /** True once stop-requested is in the scratch root: the audit is winding down. */
  stopRequested?: boolean
  /** Why the audit stopped although its register says it goes on: its process, or its launcher, has ended. */
  stopped?: string
  counts?: Counts
  errors?: ErrorRow[]
  agent?: string
  agentsDone?: number
  agentsTotal?: number
  iterations?: number
  revisions?: number
  resumes?: number
  session?: Window
  week?: Window
  turns?: number
  tokens?: number
  cost?: number
  commits?: number
  guards?: number
  result?: string
  consumption?: string
  updatedAt: number
}

declare module 'claude-code' {
  interface PluginState {
    'specaudit-monitor': {
      snapshot: Snapshot | null
      tick: number
      /** The pane's collapsible section the person unfolded, by title (one at most: an accordion); they start folded. */
      unfolded: string[]
      /** The error whose detail the person unfolded, by id (one at most). */
      opened: string[]
      /** When the band's stop button was first pressed (ms), 0 otherwise: a second press within 10 s confirms. */
      armed: number
    }
  }
}
