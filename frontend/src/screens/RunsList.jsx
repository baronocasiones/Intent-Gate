// src/screens/RunsList.jsx — S0, default route #/runs
// Data: getRuns() from seam only. No fetch, no inline arrays.
import { useEffect, useState } from 'react'
import { getRuns } from '../data/index.js'
import { resolveStatus, resolveGate } from '../domain/verdicts.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import styles from './RunsList.module.css'

const ALL = 'all'

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' · ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export default function RunsList() {
  const [runs, setRuns] = useState(null)   // null = loading
  const [statusFilter, setStatusFilter] = useState(ALL)
  const [repoFilter, setRepoFilter] = useState(ALL)

  useEffect(() => {
    getRuns().then(setRuns)
  }, [])

  // Derive repo list from loaded data
  const repos = runs
    ? [ALL, ...Array.from(new Set(runs.map(r => r.repository)))]
    : [ALL]

  const filtered = (runs ?? []).filter(r => {
    const statusOk = statusFilter === ALL || r.status === statusFilter
    const repoOk = repoFilter === ALL || r.repository === repoFilter
    return statusOk && repoOk
  })

  return (
    <div className={styles.page}>
      {/* Page header */}
      <div className={styles.header}>
        <h1 className={styles.title}>Verification Runs</h1>
        <Button variant="primary">SET UP REPOSITORY +</Button>
      </div>

      {/* Filter row */}
      <div className={styles.filters}>
        {/* Search */}
        <div className={styles.searchWrap}>
          <span className={styles.searchIcon} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--violet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>
          <input
            className={styles.searchInput}
            type="search"
            placeholder="Search runs, PRs, commits…"
            aria-label="Search runs"
          />
        </div>
        {/* Repository filter */}
        <div className={styles.selectWrap}>
          <label className={styles.filterLabel} htmlFor="filter-repo">
            <span className="micro-label">Repository</span>
          </label>
          <select
            id="filter-repo"
            className={styles.filterSelect}
            value={repoFilter}
            onChange={e => setRepoFilter(e.target.value)}
          >
            {repos.map(r => (
              <option key={r} value={r}>{r === ALL ? 'All repositories' : r}</option>
            ))}
          </select>
        </div>
        {/* Status filter */}
        <div className={styles.selectWrap}>
          <label className={styles.filterLabel} htmlFor="filter-status">
            <span className="micro-label">Status</span>
          </label>
          <select
            id="filter-status"
            className={styles.filterSelect}
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value={ALL}>All statuses</option>
            <option value="certified">Complete</option>
            <option value="running">In Progress</option>
            <option value="rejected">Rejected</option>
            <option value="failed">Failed</option>
            <option value="queued">Queued</option>
          </select>
        </div>
      </div>

      {/* Table — real table semantics; loading/empty render OUTSIDE the table so
          the row/column structure stays valid for assistive tech. */}
      <div className={styles.tableWrap}>
        {/* Loading skeleton */}
        {runs === null && (
          <div className={styles.skeletonList} role="status" aria-live="polite" aria-label="Loading runs">
            {[1, 2, 3].map(i => (
              <div key={i} className={styles.skeletonRow}>
                <div className={styles.skeletonCell} style={{ width: '35%' }} />
                <div className={styles.skeletonCell} style={{ width: '18%' }} />
                <div className={styles.skeletonCell} style={{ width: '8%' }} />
                <div className={styles.skeletonCell} style={{ width: '10%' }} />
                <div className={styles.skeletonCell} style={{ width: '10%' }} />
                <div className={styles.skeletonCell} style={{ width: '12%' }} />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {runs !== null && filtered.length === 0 && (
          <EmptyState
            title="No verification runs"
            message={
              statusFilter !== ALL || repoFilter !== ALL
                ? 'No runs match the current filters. Try clearing them.'
                : 'No runs have been triggered yet. Set up a repository to get started.'
            }
          />
        )}

        {filtered.length > 0 && (
          <div role="table" aria-label="Verification runs">
            {/* Column headers */}
            <div role="rowgroup" className={styles.colHeaders}>
              <span role="columnheader" className="micro-label">Pull Request</span>
              <span role="columnheader" className="micro-label">Repository</span>
              <span role="columnheader" className="micro-label">Commit</span>
              <span role="columnheader" className="micro-label">Run Status</span>
              <span role="columnheader" className="micro-label">Gate Decision</span>
              <span role="columnheader" className="micro-label">Started</span>
              <span role="columnheader" aria-hidden="true" />
            </div>

            <div role="rowgroup">
              {filtered.map(run => {
                const status = resolveStatus(run.status)
                const gate = resolveGate(run.exit_code)
                return (
                  <div key={run.run_id} role="row" className={styles.row}>
                    <span role="cell" className={styles.prCell}>
                      <a
                        href={`#/runs/${run.run_id}`}
                        className={styles.prLink}
                      >
                        {run.pull_request}
                      </a>
                    </span>
                    <span role="cell" className={styles.repoCell}>{run.repository}</span>
                    <span role="cell" className={styles.commitCell}>
                      <code className={styles.mono}>{run.commit}</code>
                    </span>
                    <span role="cell" className={styles.statusCell}>
                      <Badge variant={status.pill}>{status.label}</Badge>
                    </span>
                    <span role="cell" className={styles.gateCell}>
                      <Badge variant={gate.pill}>{gate.label}</Badge>
                    </span>
                    <span role="cell" className={styles.dateCell}>{formatDate(run.started)}</span>
                    <span role="cell" className={styles.actionCell}>
                      <a href={`#/runs/${run.run_id}`} className={styles.viewLink}>
                        View Run ›
                      </a>
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
