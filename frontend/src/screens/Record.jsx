// src/screens/Record.jsx — S7 #/runs/:id/record
// Traceability table, exclusions, export JSON
import { useEffect, useState } from 'react'
import { getRun, getTraceability } from '../data/index.js'
import { resolveVerdict, resolveGate } from '../domain/verdicts.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import styles from './Record.module.css'

export default function Record({ runId }) {
  const [run, setRun] = useState(null)
  const [traceability, setTraceability] = useState(null)

  useEffect(() => {
    getRun(runId).then(setRun)
    getTraceability(runId).then(setTraceability)
  }, [runId])

  if (!run || !traceability) return (
    <div className={styles.page} aria-busy="true">
      <div className={styles.skeleton} style={{ height: 160 }} />
      <div className={styles.skeleton} style={{ height: 300 }} />
    </div>
  )

  const gate = resolveGate(run.exit_code ?? 1)
  const verdicts = run.verdicts ?? []
  const links = traceability.links ?? []

  // Merge: each link row, enriched with verdict info
  const rows = links.map(link => {
    const verdict = verdicts.find(v => v.criterion_id === link.criterion_id)
    return { ...link, verdict }
  })

  function exportJSON() {
    const blob = new Blob([JSON.stringify(run, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `run-${run.run_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Verification Record</h1>
      </div>

      {/* Run header grid */}
      <div className={styles.runHeader}>
        <div className={styles.runField}>
          <span className="micro-label">Run ID</span>
          <code className={styles.mono}>{run.run_id}</code>
        </div>
        <div className={styles.runField}>
          <span className="micro-label">Repository · PR</span>
          <span>user/payments-api · #482</span>
        </div>
        <div className={styles.runField}>
          <span className="micro-label">Verified Commit</span>
          <code className={styles.mono}>a3f9c12</code>
        </div>
        <div className={styles.runField}>
          <span className="micro-label">Completed</span>
          <span>15 Jan 2026 · 15:22</span>
        </div>
        <div className={styles.runField}>
          <span className="micro-label">Policy Version</span>
          <span>block-merge v1</span>
        </div>
        <div className={styles.runField}>
          <span className="micro-label">Gate Decision</span>
          <Badge variant={gate.pill}>{gate.label}</Badge>
        </div>
      </div>

      {/* Traceability table */}
      <div className={styles.card}>
        <span className="micro-label">Requirement-to-Code-to-Test Traceability</span>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col" className="micro-label">Requirement</th>
              <th scope="col" className="micro-label">Code Evidence</th>
              <th scope="col" className="micro-label">Test Evidence</th>
              <th scope="col" className="micro-label">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => {
              const vr = resolveVerdict(row.verdict?.verdict)
              return (
                <tr key={row.criterion_id} className={styles.tableRow}>
                  <td className={styles.reqCell}>
                    <code className={styles.critId}>{row.criterion_id}</code>
                    <span className={styles.reqText}>{row.verdict?.rationale?.slice(0, 80)}…</span>
                  </td>
                  <td className={styles.codeCell}>
                    {row.locations?.length > 0
                      ? row.locations.map((loc, i) => (
                          <code key={i} className={styles.loc}>{loc}</code>
                        ))
                      : <span className={styles.absent}>—</span>
                    }
                  </td>
                  <td className={styles.testCell}>
                    <span className={styles.absent}>—</span>
                  </td>
                  <td>
                    <Badge variant={vr.pill}>{vr.label}</Badge>
                  </td>
                </tr>
              )
            })}
            {/* Not-verified row (mock always has one) */}
            <tr className={`${styles.tableRow} ${styles.tableRowNotVerified}`}>
              <td className={styles.reqCell}>
                <code className={styles.critId}>AC-3</code>
                <span className={styles.reqText}>Rate-limit failed login attempts at the gateway level.</span>
              </td>
              <td><span className={styles.absent}>—</span></td>
              <td><span className={styles.absent}>—</span></td>
              <td><Badge variant="idle">Not Verified</Badge></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Excluded and unresolved */}
      <div className={styles.sunken}>
        <span className="micro-label">Excluded and Unresolved Requirements</span>
        <p className={styles.sunkenText}>No requirements were excluded from this run.</p>
      </div>

      {/* What was not verified */}
      <div className={styles.sunken}>
        <span className="micro-label">What Was Not Verified</span>
        <ul className={styles.bulletList}>
          <li>AC-3 — Rate-limiting criterion not in scope of this PR.</li>
          <li>Error-path retry behaviour for the gateway call was not adversarially checked.</li>
        </ul>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <button
          type="button"
          className={styles.footLink}
          disabled
          title="Not reachable in the static preview"
        >
          Open Pull Request ›
        </button>
        <button
          type="button"
          className={styles.footLink}
          disabled
          title="Not reachable in the static preview"
        >
          View Evidence ›
        </button>
        <Button variant="primary" onClick={exportJSON}>EXPORT JSON ↓</Button>
      </div>
    </div>
  )
}
