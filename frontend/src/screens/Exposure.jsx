// src/screens/Exposure.jsx — S8 #/exposure
// Big false_certified_rate number, coverage trend SVG, capability breakdown
import { useEffect, useState } from 'react'
import { getExposure } from '../data/index.js'
import styles from './Exposure.module.css'

const OPERATORS = [
  'boundary_drop', 'comparison_inversion', 'threshold_weakening',
  'error_path_deletion', 'normative_demotion', 'negative_constraint_removal',
  'untestability',
]

const OP_LABELS = {
  boundary_drop:               'Boundary Drop',
  comparison_inversion:        'Comparison Inversion',
  threshold_weakening:         'Threshold Weakening',
  error_path_deletion:         'Error Path Deletion',
  normative_demotion:          'Normative Demotion',
  negative_constraint_removal: 'Negative Constraint Removal',
  untestability:               'Untestability',
}

// Simple SVG trend line — no chart library
function TrendLine({ points }) {
  if (!points.length) return null
  const W = 560, H = 120, PAD = 12
  const xs = points.map((_, i) => PAD + (i / (points.length - 1 || 1)) * (W - PAD * 2))
  const maxV = Math.max(...points, 1)
  const ys = points.map(v => H - PAD - (v / maxV) * (H - PAD * 2))
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x},${ys[i]}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={styles.trendSvg} aria-label="Coverage trend line chart" role="img">
      <polyline points={xs.map((x, i) => `${x},${H - PAD}`).join(' ')} fill="none" stroke="transparent" />
      <path d={d} fill="none" stroke="var(--violet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {xs.map((x, i) => <circle key={i} cx={x} cy={ys[i]} r="3" fill="var(--violet)" />)}
    </svg>
  )
}

// Demo trend data (Phase A origin — no contract for this)
const TREND = [0.42, 0.38, 0.31, 0.28, 0.25]
const TREND_LABELS = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan']

export default function Exposure() {
  const [exposure, setExposure] = useState(null)
  const [repo, setRepo] = useState('all')
  const [period, setPeriod] = useState('all')

  useEffect(() => {
    getExposure().then(setExposure)
  }, [])

  if (!exposure) return (
    <div className={styles.page} aria-busy="true">
      <div className={styles.skeleton} style={{ height: 200 }} />
    </div>
  )

  const { false_certified_rate, measured, by_operator } = exposure

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Exposure</h1>
        {/* Filters */}
        <div className={styles.filters}>
          <select className={styles.filterSelect} value={repo} onChange={e => setRepo(e.target.value)} aria-label="Repository filter">
            <option value="all">All repositories</option>
            <option value="payments">user/payments-api</option>
            <option value="identity">user/identity-service</option>
          </select>
          <select className={styles.filterSelect} value={period} onChange={e => setPeriod(e.target.value)} aria-label="Period filter">
            <option value="all">All time</option>
            <option value="q1">Q1 2026</option>
            <option value="q4">Q4 2025</option>
          </select>
        </div>
      </div>

      {/* Focal point — the big number */}
      <div className={styles.statCard}>
        <span className="micro-label">Requirements Without Completed Verification</span>
        {measured ? (
          <>
            <p className={styles.statNum}>
              {Math.round(false_certified_rate * 100)}%
            </p>
            <p className={styles.statCaption}>
              False-certified rate — {Math.round(false_certified_rate * 100)}% of verified requirements
              may have been certified without sufficient evidence.
            </p>
          </>
        ) : (
          <>
            <p className={`${styles.statNum} ${styles.unmeasured}`}>
              unmeasured
            </p>
            <p className={styles.statCaption}>
              No measurement data is available. Run a full adversarial verification to generate exposure metrics.
            </p>
          </>
        )}
      </div>

      {/* Coverage trend */}
      <div className={styles.card}>
        <span className="micro-label">Coverage Trend</span>
        <TrendLine points={TREND} />
        <div className={styles.trendLabels} aria-hidden="true">
          {TREND_LABELS.map(l => <span key={l} className={styles.trendLabel}>{l}</span>)}
        </div>
        <p className={styles.trendNote}>Phase A demo trend — not captured from live runs.</p>
      </div>

      {/* Capability breakdown */}
      <div className={styles.card}>
        <span className="micro-label">Capability Breakdown</span>
        <div className={styles.opList}>
          {OPERATORS.map(op => {
            const data = by_operator?.[op]
            const total = data?.total ?? 0
            const certified = data?.certified ?? 0
            const pct = total > 0 ? Math.round((certified / total) * 100) : null
            return (
              <div key={op} className={styles.opRow}>
                <span className={styles.opLabel}>{OP_LABELS[op]}</span>
                {pct !== null ? (
                  <>
                    <div
                      className={styles.opTrack}
                      role="progressbar"
                      aria-valuenow={pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${OP_LABELS[op]}: ${pct}% complete`}
                    >
                      <div className={styles.opFill} style={{ width: `${pct}%` }} />
                    </div>
                    <span className={styles.opPct}>{pct}% Complete</span>
                  </>
                ) : (
                  <span className={styles.opPctMuted}>—</span>
                )}
                <button
                  type="button"
                  className={styles.opLink}
                  disabled
                  title="Not reachable in the static preview"
                >
                  View Uncovered Requirements ›
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* By-operator detail (disclosure) */}
      <details className={styles.details}>
        <summary className={styles.detailsSummary}>
          <span className="micro-label">By-Operator Raw Breakdown</span>
        </summary>
        <table className={styles.opTable}>
          <thead>
            <tr>
              <th scope="col" className="micro-label">Operator</th>
              <th scope="col" className="micro-label">Certified</th>
              <th scope="col" className="micro-label">Total</th>
            </tr>
          </thead>
          <tbody>
            {OPERATORS.map(op => (
              <tr key={op} className={styles.opTableRow}>
                <td>{OP_LABELS[op]}</td>
                <td>{by_operator?.[op]?.certified ?? '—'}</td>
                <td>{by_operator?.[op]?.total ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}
