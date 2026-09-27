// src/data/index.js — THE SEAM (§5.3)
// This is the ONLY file that knows where data comes from.
// Phase A: reads static JSON files. No screen may call fetch() (the legacy api.js was retired).
// Phase B: swap the internals here; every screen stays unchanged.

import { ACTIVE_SCENARIO } from './scenarios.js'

// ─── Static imports (Phase A) ────────────────────────────────────────────────
import demoRun        from './static/demo_run.json'
import demoTraceability from './static/demo_traceability.json'
import demoExposure   from './static/demo_exposure.json'
import runsData       from './static/runs.json'
import progressData   from './static/progress.json'

// ─── Scenario overrides ───────────────────────────────────────────────────────
function applyScenario_Run(run) {
  switch (ACTIVE_SCENARIO) {
    case 'zero-criteria':
      return { ...run, verdicts: [] }
    case 'many-locations':
      return {
        ...run,
        verdicts: run.verdicts.map(v => ({
          ...v,
          locations: [
            'src/refund.py:12', 'src/refund.py:34', 'src/refund.py:56',
            'src/refund.py:78', 'src/refund.py:99', 'src/payment_gateway.py:201',
            'src/payment_gateway.py:215', 'tests/test_refund.py:44',
          ],
        })),
      }
    case 'in-progress':
      return { ...run, status: 'running', exit_code: null }
    default:
      return run
  }
}

function applyScenario_Runs(runs) {
  if (ACTIVE_SCENARIO === 'empty') return []
  if (ACTIVE_SCENARIO === 'in-progress') {
    return runs.map(r => r.run_id === 'demo' ? { ...r, status: 'running', exit_code: null } : r)
  }
  return runs
}

function applyScenario_Exposure(exp) {
  if (ACTIVE_SCENARIO === 'unmeasured') {
    return { ...exp, false_certified_rate: null, measured: false }
  }
  return exp
}

// ─── Public API ───────────────────────────────────────────────────────────────

/** Returns the data source mode. Phase A always returns 'static'. */
export async function getSource() {
  return 'static'
}

/** Returns the list of runs. */
export async function getRuns() {
  const runs = applyScenario_Runs(runsData.runs)
  return runs
}

/** Returns a single run by id, or the demo run if id not found. */
export async function getRun(id) {
  const run = id === 'demo' || !id ? demoRun : demoRun
  return applyScenario_Run(run)
}

/** Returns the traceability data for a run. */
export async function getTraceability(id) {
  return demoTraceability
}

/** Returns the exposure metrics. */
export async function getExposure() {
  return applyScenario_Exposure(demoExposure)
}

/** Returns in-progress state for the verifying screen. */
export async function getProgress(id) {
  const p = progressData
  if (ACTIVE_SCENARIO === 'in-progress') {
    return { ...p, completed: 1, total: 7 }
  }
  return p
}
