// src/screens/AuditHistory.jsx — S9 #/audit
// Designed from the system: period control, filter chips, run list, export
import { useEffect, useState } from 'react'
import { getRuns } from '../data/index.js'
import { resolveVerdict, resolveGate } from '../domain/verdicts.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import styles from './AuditHistory.module.css'

const PERIODS = ['All', 'Q1', 'Q2', 'Q3', 'Q4']
const FILTER_CHIPS = ['date', 'capability', 'verdict']

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// Map run status to audit outcome pill
function auditOutcome(run) {
  if (run.exit_code === 0) return { label: 'PASS', variant: 'ok' }
  if (run.status === 'running') return { label: 'IN PROGRESS', variant: 'info' }
  return { label: 'FAIL', variant: 'bad' }
}

export default function AuditHistory() {
  const [runs, setRuns] = useState(null)
  const [period, setPeriod] = useState('All')
  const [activeChips, setActiveChips] = useState(new Set())

  useEffect(() => { getRuns().then(setRuns) }, [])

  function toggleChip(chip) {
    setActiveChips(prev => {
      const next = new Set(prev)
      next.has(chip) ? next.delete(chip) : next.add(chip)
      return next
    })
  }

  function exportAudit() {
    const blob = new Blob(
      [JSON.stringify(runs ?? [], null, 2)],
      { type: 'application/json' }
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit-export.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const displayRuns = runs ?? []

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Audit History</h1>
        <Button variant="primary" onClick={exportAudit}>Export for auditor ↓</Button>
      </div>

      {/* Period segmented control */}
      <div className={styles.periodRow} role="group" aria-label="Period filter">
        {PERIODS.map(p => (
          <button
            key={p}
            type="button"
            className={`${styles.periodBtn} ${period === p ? styles.periodBtnActive : ''}`}
            onClick={() => setPeriod(p)}
            aria-pressed={period === p}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Filter chips */}
      <div className={styles.chipsRow} role="group" aria-label="Active filters">
        <span className="micro-label" style={{ alignSelf: 'center' }}>Filter by</span>
        {FILTER_CHIPS.map(chip => (
          <button
            key={chip}
            type="button"
            className={`${styles.chip} ${activeChips.has(chip) ? styles.chipActive : ''}`}
            onClick={() => toggleChip(chip)}
            aria-pressed={activeChips.has(chip)}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Run list */}
      <div className={styles.list} role="region" aria-label="Audit run list">
        {runs === null && (
          <div className={styles.skeletonList} aria-busy="true">
            {[1,2,3].map(i => <div key={i} className={styles.skeletonRow} />)}
          </div>
        )}
        {runs !== null && displayRuns.length === 0 && (
          <EmptyState title="No runs in this period" message="Try selecting a different period or clearing filters." />
        )}
        {displayRuns.map(run => {
          const outcome = auditOutcome(run)
          return (
            <div key={run.run_id} className={styles.row}>
              <div className={styles.rowLeft}>
                <a href={`#/runs/${run.run_id}`} className={styles.prLink}>{run.pull_request}</a>
                <span className={styles.repoMeta}>{run.repository}</span>
              </div>
              <div className={styles.rowRight}>
                <Badge variant={outcome.variant}>{outcome.label}</Badge>
                <span className={styles.dateMeta}>{formatDate(run.started)}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
