// src/data/scenarios.js
// Dev toggle for Phase A demo states (§3.8).
// Change ACTIVE_SCENARIO to exercise different states without a live API.
//
// Scenarios:
//   'default'       — the canonical demo run (mixed verdicts, real locations)
//   'empty'         — runs list is empty
//   'zero-criteria' — run has no verdicts
//   'many-locations'— run with many locations per criterion
//   'in-progress'   — run with status=running
//   'unmeasured'    — exposure with measured:false

export const ACTIVE_SCENARIO = 'default'
