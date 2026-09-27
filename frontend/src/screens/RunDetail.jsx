// src/screens/RunDetail.jsx — S5 #/runs/:id (non-running)
// Verification Results: MERGE BLOCKED banner, verdict list + detail, override modal
import { useEffect, useState, useRef } from 'react'
import { getRun } from '../data/index.js'
import { resolveStatus, resolveVerdict, resolveGate, resolveTier } from '../domain/verdicts.js'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import Modal from '../components/Modal.jsx'
import styles from './RunDetail.module.css'

const ALL = 'all'

export default function RunDetail({ runId }) {
  const [run, setRun] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [verdictFilter, setVerdictFilter] = useState(ALL)
  const [modalOpen, setModalOpen] = useState(false)
  const overrideTriggerRef = useRef(null)

  useEffect(() => {
    getRun(runId).then(r => {
      setRun(r)
      if (r?.verdicts?.length) setSelectedId(r.verdicts[0].criterion_id)
    })
  }, [runId])

  if (!run) return <div className={styles.page} aria-busy="true"><div className={styles.skeleton} style={{ height: 200 }} /></div>

  const status = resolveStatus(run.status)
  const gate = resolveGate(run.exit_code ?? 1)
  const blocked = gate.pill === 'bad'

  const verdicts = run.verdicts ?? []
  const filtered = verdicts.filter(v =>
    verdictFilter === ALL || v.verdict.toLowerCase() === verdictFilter
  )
  const selected = verdicts.find(v => v.criterion_id === selectedId)

  function openModal() { setModalOpen(true) }
  function closeModal() {
    setModalOpen(false)
    overrideTriggerRef.current?.focus()
  }

  // Tally
  const certified   = verdicts.filter(v => v.verdict === 'CERTIFIED').length
  const conditional = verdicts.filter(v => v.verdict === 'CONDITIONAL').length
  const rejected    = verdicts.filter(v => v.verdict === 'REJECTED').length

  return (
    <div className={styles.page}>
      {/* Header buttons */}
      <div className={styles.topActions}>
        <Button variant="primary" onClick={() => window.location.hash = `/runs/${runId}/confirm`}>
          RE-RUN VERIFICATION ›
        </Button>
        <Button
          variant="secondary"
          ref={overrideTriggerRef}
          onClick={openModal}
        >
          OVERRIDE GATE
        </Button>
      </div>

      {/* PR header card */}
      <div className={styles.prCard}>
        <div className={styles.prLine}>
          <h1 className={styles.prNum}>PULL REQUEST #482</h1>
          <Badge variant={status.pill}>{status.label}</Badge>
        </div>
        <p className={styles.prTitle}>Enforce supervisor approval on refunds</p>
        <div className={styles.prMeta}>
          <span>user/payments-api</span>
          <code className={styles.mono}>a3f9c12</code>
        </div>
      </div>

      {/* MERGE BLOCKED banner — the focal point */}
      <div className={`${styles.gateBanner} ${blocked ? styles.gateBlocked : styles.gateAllowed}`}>
        <div className={styles.bannerLeft}>
          <span className={styles.gateGlyph} aria-hidden="true">{blocked ? '✕' : '✓'}</span>
          <div>
            <p className={styles.gateVerdict}>{blocked ? 'MERGE BLOCKED' : 'MERGE ALLOWED'}</p>
            <p className={styles.gateTally}>
              {certified > 0 && <span>{certified} Certified</span>}
              {conditional > 0 && <span> · {conditional} Conditional</span>}
              {rejected > 0 && <span> · {rejected} Rejected</span>}
            </p>
          </div>
        </div>
        <div className={styles.bannerRight}>
          <p className={styles.bannerNote}>Requirement verdicts remain unchanged</p>
          <p className={styles.bannerDecision}>Gate decision: {gate.label}</p>
        </div>
      </div>

      {/* Two-column detail */}
      <div className={styles.detail}>
        {/* Left: verdict list */}
        <div className={styles.left}>
          <div className={styles.filterRow}>
            <label className="micro-label" htmlFor="verdict-filter">All verdicts</label>
            <select
              id="verdict-filter"
              className={styles.filterSelect}
              value={verdictFilter}
              onChange={e => setVerdictFilter(e.target.value)}
            >
              <option value={ALL}>All</option>
              <option value="certified">Certified</option>
              <option value="conditional">Conditional</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <ul className={styles.verdictList} role="list">
            {filtered.map(v => {
              const vr = resolveVerdict(v.verdict)
              return (
                <li key={v.criterion_id}>
                  <button
                    type="button"
                    className={`${styles.verdictRow} ${selectedId === v.criterion_id ? styles.verdictRowSelected : ''}`}
                    onClick={() => setSelectedId(v.criterion_id)}
                    aria-pressed={selectedId === v.criterion_id}
                  >
                    <code className={styles.critId}>{v.criterion_id}</code>
                    <Badge variant={vr.pill}>{vr.label}</Badge>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>

        {/* Right: finding detail */}
        <div className={styles.right}>
          {selected ? <FindingDetail verdict={selected} runId={runId} /> : null}
        </div>
      </div>

      <Modal open={modalOpen} onClose={closeModal} />
    </div>
  )
}

function FindingDetail({ verdict, runId }) {
  const vr = resolveVerdict(verdict.verdict)
  const tier = resolveTier(verdict.evidence_tier)

  return (
    <div className={styles.findingCard}>
      {/* Criterion header */}
      <div className={styles.findingHeader}>
        <code className={styles.critIdLarge}>{verdict.criterion_id}</code>
        <Badge variant={vr.pill}>{vr.label}</Badge>
      </div>

      {/* Read-Only Attestation callout */}
      <div className={styles.attestCallout}>
        <span className={styles.attestIcon} aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </span>
        <span>Read-Only Attestation — the verifier inspected code but did not modify it.</span>
      </div>

      {/* Original source */}
      <div className={styles.findingSection}>
        <span className="micro-label">Original Source</span>
        <blockquote className={styles.sourceQuote}>
          The system must enforce approval of a supervisor before processing any refund request.
        </blockquote>
      </div>

      {/* Explanation / rationale */}
      <div className={styles.findingSection}>
        <span className="micro-label">Explanation</span>
        <p className={styles.findingText}>{verdict.rationale ?? '—'}</p>
      </div>

      {/* Code evidence block */}
      {verdict.locations?.length > 0 && (
        <div className={styles.findingSection}>
          <span className="micro-label">Code Evidence</span>
          {verdict.locations.map((loc, i) => {
            const [filePath, line] = loc.split(':')
            return (
              <div key={i} className={styles.codeBlock}>
                <div className={styles.codeHeader}>
                  <span className={styles.codePath}>{filePath}</span>
                  {line && <span className={styles.codeLine}>Line {line}</span>}
                </div>
                <pre className={styles.codePre}><code>{loc}</code></pre>
              </div>
            )
          })}
        </div>
      )}
      {!verdict.locations?.length && (
        <div className={styles.findingSection}>
          <span className="micro-label">Code Evidence</span>
          <p className={styles.absent}>—</p>
        </div>
      )}

      {/* Evidence level */}
      <div className={styles.findingSection}>
        <span className="micro-label">Evidence Level</span>
        {tier ? (
          <div className={styles.tierRow}>
            <Badge variant={verdict.verdict === 'CERTIFIED' && verdict.evidence_tier !== 'E0' ? 'ok' : 'idle'}>
              {tier.short}
            </Badge>
            <span className={styles.tierDesc}>{tier.desc}</span>
          </div>
        ) : <span className={styles.absent}>—</span>}
      </div>

      {/* Footer links — the two source targets have no destination in a static
          preview, so they are disabled buttons rather than dead href="#" links. */}
      <div className={styles.findingFooter}>
        <button
          type="button"
          className={styles.footLink}
          disabled
          title="Source host is not connected in the static preview"
        >
          View Code ›
        </button>
        <button
          type="button"
          className={styles.footLink}
          disabled
          title="Source host is not connected in the static preview"
        >
          View Source ›
        </button>
        <a href={`#/runs/${runId}/record`} className={`${styles.footLink} ${styles.footLinkPrimary}`}>VIEW VERIFICATION RECORD ›</a>
      </div>
    </div>
  )
}
