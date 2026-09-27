// src/screens/Verifying.jsx — S4 #/runs/:id (when status=running)
// RUNNING bar, progress card, worker log, cancel button
import { useEffect, useRef, useState } from 'react'
import { getRun, getProgress } from '../data/index.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import styles from './Verifying.module.css'

export default function Verifying({ runId }) {
  const [run, setRun] = useState(null)
  const [progress, setProgress] = useState(null)
  const logRef = useRef(null)

  useEffect(() => {
    getRun(runId).then(setRun)
    getProgress(runId).then(setProgress)
  }, [runId])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [progress])

  if (!run || !progress) return (
    <div className={styles.page} aria-busy="true">
      <div className={styles.runningBar} />
      <div className={styles.skeleton} style={{ height: 120 }} />
      <div className={styles.skeleton} style={{ height: 300 }} />
    </div>
  )

  const pct = Math.min(100, Math.round((progress.completed / progress.total) * 100))

  return (
    <div className={styles.page}>
      {/* Running status bar */}
      <div className={styles.runningBar} role="status" aria-label="Verification in progress">
        <span className={styles.runningDot} aria-hidden="true" />
        RUNNING
      </div>

      {/* PR header card */}
      <div className={styles.prCard}>
        <div className={styles.prLeft}>
          <div className={styles.prLine}>
            <h1 className={styles.prNum}>PULL REQUEST #482</h1>
            <Badge variant="info">In Progress</Badge>
          </div>
          <p className={styles.prTitle}>Enforce supervisor approval on refunds</p>
          <div className={styles.prMeta}>
            <span>user/payments-api</span>
            <span className={styles.mono}>a3f9c12</span>
          </div>
        </div>
      </div>

      {/* Progress card */}
      <div className={styles.progressCard}>
        {/* Chips */}
        <div className={styles.chips}>
          <span className={styles.chip}>{progress.workers} Parallel Workers</span>
          <span className={styles.chip}>Read-Only Verifier</span>
        </div>

        {/* Counter */}
        <div className={styles.counter} aria-live="polite">
          <span className={styles.counterNum}>{progress.completed} OF {progress.total}</span>
          <span className={styles.counterLabel}>requirements completed</span>
        </div>

        {/* Progress bar */}
        <div
          className={styles.progressTrack}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${pct}% complete`}
        >
          <div className={styles.progressFill} style={{ width: `${pct}%` }} />
        </div>
        <span className={styles.pctLabel}>{pct}%</span>

        {/* Current activity */}
        <p className={styles.currentActivity}>
          <strong>Current Activity:</strong> {progress.current_activity}
        </p>

        {/* Read-only sentence — verbatim, §5 Prompt 5 */}
        <div className={styles.readOnlyNote}>
          Workers can inspect repository content and evidence, but cannot edit code or execute repository commands.
        </div>

        {/* Requirement rows */}
        <div className={styles.reqRows}>
          {progress.requirements.map((req, i) => (
            <div key={req.criterion_id} className={`${styles.reqRow} ${styles[`reqRow_${req.state}`]}`}>
              {req.state === 'complete' && (
                <span className={styles.checkIcon} role="img" aria-label="Complete">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--ok-ink)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </span>
              )}
              {/* Position marker only — the status word beside it carries the meaning */}
              {req.state === 'checking' && (
                <span className={styles.reqIndex} aria-hidden="true">{i + 1}</span>
              )}
              {req.state === 'queued' && (
                <span className={styles.reqIndex} aria-hidden="true">{i + 1}</span>
              )}
              <span className={styles.reqId}>{req.criterion_id}</span>
              <span className={`${styles.reqStatus} ${styles[`reqStatus_${req.state}`]}`}>
                {req.state === 'complete' ? 'Complete' : req.state === 'checking' ? 'Checking' : 'Queued'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Worker log — Phase A demo content, labelled as such */}
      <div className={styles.logSection}>
        <div className={styles.logHeader}>
          <span className="micro-label" style={{ color: 'var(--text-muted)' }}>Worker Activity Details</span>
          <Badge variant="idle">Demo content — not captured output</Badge>
        </div>
        <div className={styles.logPanel} ref={logRef} role="log" aria-label="Worker activity log" aria-live="polite">
          {progress.log.map((entry, i) => (
            <div key={i} className={styles.logLine}>
              <span className={styles.logTs}>{entry.ts}</span>
              <span className={styles.logMsg}>{entry.msg}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Cancel — danger button, bottom-right */}
      <div className={styles.cancelRow}>
        <Button
          variant="danger"
          onClick={() => window.location.hash = '/runs'}
        >
          CANCEL VERIFICATION
        </Button>
      </div>
    </div>
  )
}
