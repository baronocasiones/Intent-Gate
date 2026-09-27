// src/domain/verdicts.js
// Single home for all status/verdict/tier → label + pill-variant mappings.
// Normalises case here so callers never need to uppercase anything.

// Run status
export const STATUS_MAP = {
  queued:      { label: 'Queued',      pill: 'idle' },
  running:     { label: 'In Progress', pill: 'info' },
  certified:   { label: 'Complete',    pill: 'ok'   },
  conditional: { label: 'Conditional', pill: 'warn' },
  rejected:    { label: 'Rejected',    pill: 'bad'  },
  failed:      { label: 'Failed',      pill: 'bad'  },
  pending:     { label: 'Pending',     pill: 'idle' },
}

// exit_code → gate decision
export const GATE_MAP = {
  0:    { label: 'Allowed',  pill: 'ok'  },
  null: { label: 'Blocked',  pill: 'bad' },
  1:    { label: 'Blocked',  pill: 'bad' },
}

// verdict enum
export const VERDICT_MAP = {
  CERTIFIED:   { label: 'Certified',    pill: 'ok'   },
  CONDITIONAL: { label: 'Conditional',  pill: 'warn' },
  REJECTED:    { label: 'Rejected',     pill: 'bad'  },
  PENDING:     { label: 'Not Verified', pill: 'idle' },
}

// Evidence tier descriptions (E0–E6)
export const TIER_LABELS = {
  E0: { short: 'E0', desc: 'None'              },
  E1: { short: 'E1', desc: 'Asserted'          },
  E2: { short: 'E2', desc: 'Located'           },
  E3: { short: 'E3', desc: 'Traced'            },
  E4: { short: 'E4', desc: 'Exercised'         },
  E5: { short: 'E5', desc: 'Refuted-checked'   },
  E6: { short: 'E6', desc: 'Corroborated'      },
}

/** Resolve run status → { label, pill }. Input may be any case. */
export function resolveStatus(raw) {
  if (!raw) return { label: 'Unknown', pill: 'idle' }
  return STATUS_MAP[raw.toLowerCase()] ?? { label: raw, pill: 'idle' }
}

/** Resolve verdict enum → { label, pill }. Input must be uppercase (contract). */
export function resolveVerdict(raw) {
  if (!raw) return { label: 'Not Verified', pill: 'idle' }
  return VERDICT_MAP[raw.toUpperCase()] ?? { label: raw, pill: 'idle' }
}

/** Resolve gate from exit_code. */
export function resolveGate(exitCode) {
  if (exitCode === 0) return GATE_MAP[0]
  return GATE_MAP[1]
}

/** Resolve evidence tier. */
export function resolveTier(raw) {
  if (!raw) return null
  return TIER_LABELS[raw.toUpperCase()] ?? { short: raw, desc: '' }
}
