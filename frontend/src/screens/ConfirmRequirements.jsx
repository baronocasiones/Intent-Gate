// src/screens/ConfirmRequirements.jsx — S3 #/runs/:id/confirm
// Key screen: left = requirement row-cards, right = interpretation panel
// Data: getRun() from seam; criteria derived from verdicts[].
import { useEffect, useState } from 'react'
import { getRun } from '../data/index.js'
import { resolveVerdict } from '../domain/verdicts.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import styles from './ConfirmRequirements.module.css'

export default function ConfirmRequirements({ runId }) {
  const [run, setRun] = useState(null)
  const [excluded, setExcluded] = useState(new Set())
  const [selected, setSelected] = useState(null)   // criterion_id

  useEffect(() => {
    getRun(runId).then(r => {
      setRun(r)
      if (r?.verdicts?.length) setSelected(r.verdicts[0].criterion_id)
    })
  }, [runId])

  if (!run) return (
    <div className={styles.page}>
      <div className={styles.skeletonHeader} aria-busy="true" />
      <div className={styles.body}>
        <div className={styles.skeletonLeft} />
        <div className={styles.skeletonRight} />
      </div>
    </div>
  )

  const verdicts = run.verdicts ?? []
  const excludedVerdicts = verdicts.filter(v => excluded.has(v.criterion_id))
  const unclearCount = verdicts.filter(v => v.verdict === 'CONDITIONAL').length
  const allUnclearHandled = excludedVerdicts.length >= unclearCount
  const canStart = verdicts.length > 0 && (unclearCount === 0 || allUnclearHandled)

  const selectedVerdict = verdicts.find(v => v.criterion_id === selected)

  function toggleExclude(id) {
    setExcluded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className={styles.page}>
      {/* Page header card */}
      <div className={styles.headerCard}>
        <div className={styles.headerLeft}>
          <div className={styles.prLine}>
            <h1 className={styles.prNum}>PULL REQUEST #482</h1>
            <Badge variant="info">Requirements Ready</Badge>
          </div>
          <p className={styles.prTitle}>Enforce supervisor approval on refunds</p>
        </div>
        <div className={styles.headerMeta}>
          <div className={styles.metaItem}>
            <span className="micro-label">Repository</span>
            <span className={styles.metaVal}>user/payments-api</span>
          </div>
          <div className={styles.metaItem}>
            <span className="micro-label">Branch</span>
            <span className={styles.metaVal}>feat/supervisor-approval</span>
          </div>
          <div className={styles.metaItem}>
            <span className="micro-label">Verified Commit</span>
            <code className={styles.mono}>a3f9c12</code>
          </div>
        </div>
      </div>

      {/* Two-column body */}
      <div className={styles.body}>
        {/* Left: requirement list */}
        <div className={styles.left}>
          <span className="micro-label" style={{ padding: '0 var(--s1)' }}>Requirements</span>

          {verdicts.length === 0 && (
            <EmptyState
              title="No requirements found"
              message="Intent Gate could not extract acceptance criteria from the linked ticket."
            />
          )}

          <ul className={styles.reqList} role="list">
            {verdicts.map(v => {
              const isExcluded = excluded.has(v.criterion_id)
              const isSelected = selected === v.criterion_id
              const verdict = resolveVerdict(v.verdict)
              return (
                <li
                  key={v.criterion_id}
                  className={`${styles.reqRow} ${isSelected ? styles.reqRowSelected : ''} ${isExcluded ? styles.reqRowExcluded : ''}`}
                >
                  {/* Selecting the requirement — a button, but NOT a wrapper around
                      the checkbox (nested interactive content is invalid) */}
                  <button
                    type="button"
                    className={styles.reqSelect}
                    onClick={() => setSelected(v.criterion_id)}
                    aria-pressed={isSelected}
                  >
                    <span className={styles.reqTop}>
                      <span className={styles.reqId}>{v.criterion_id}</span>
                      <Badge variant={verdict.pill}>{verdict.label}</Badge>
                    </span>
                    <span className={styles.reqText}>{v.rationale?.slice(0, 120)}{v.rationale?.length > 120 ? '…' : ''}</span>
                  </button>
                  <label className={styles.includeLabel}>
                    <input
                      type="checkbox"
                      name="include"
                      id={`include-${v.criterion_id}`}
                      checked={!isExcluded}
                      onChange={() => toggleExclude(v.criterion_id)}
                      aria-label={`Include ${v.criterion_id}`}
                    />
                    <span>Include</span>
                  </label>
                </li>
              )
            })}
          </ul>

          {/* + Add Requirement dashed row */}
          <button type="button" className={styles.addRow} aria-label="Add requirement">
            + Add Requirement
          </button>

          {/* Footer tally */}
          <div className={styles.tally}>
            <span>
              <strong>{verdicts.length - excluded.size}</strong> Ready
              {unclearCount > 0 && <> · <strong className={styles.unclear}>{unclearCount}</strong> Unclear</>}
            </span>
            {excluded.size > 0 && !allUnclearHandled && (
              <p className={styles.tallyWarn}>Add a reason for each excluded requirement.</p>
            )}
            <Button
              variant="primary"
              disabled={!canStart}
              onClick={() => window.location.hash = `/runs/${runId}`}
            >
              START VERIFICATION ›
            </Button>
          </div>
        </div>

        {/* Right: interpretation panel */}
        <div className={styles.right}>
          {selectedVerdict ? (
            <div className={styles.interpretCard}>
              <span className="micro-label">Requirement Interpretation</span>
              <div className={styles.interpretField}>
                <span className={styles.interpretFieldLabel}>Extracted requirement</span>
                <p className={styles.interpretText}>{selectedVerdict.rationale}</p>
              </div>
              <div className={styles.interpretField}>
                <span className={styles.interpretFieldLabel}>Expected outcome</span>
                <p className={styles.interpretText}>
                  {selectedVerdict.verdict === 'CERTIFIED'
                    ? 'Criterion is satisfied when this code path is exercised under test.'
                    : 'Criterion is not yet satisfied — see evidence below.'}
                </p>
              </div>
              <div className={styles.sunkenSource}>
                <div className={styles.sourceHeader}>
                  <span className="micro-label">Original Source · Read Only</span>
                  <button
                    type="button"
                    className={styles.openSource}
                    disabled
                    title="Source document is not reachable in the static preview"
                  >
                    Open Source ›
                  </button>
                </div>
                <blockquote className={styles.sourceQuote}>
                  The system must enforce approval of a supervisor before processing any refund request.
                </blockquote>
                <p className={styles.sourceNote}>Editing the interpretation above does not change the source document.</p>
              </div>
            </div>
          ) : (
            <EmptyState title="Select a requirement" message="Click a requirement on the left to see its interpretation." />
          )}
        </div>
      </div>
    </div>
  )
}
