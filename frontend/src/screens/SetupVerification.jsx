// src/screens/SetupVerification.jsx — S1 #/setup
// Sections: CONNECT GITHUB, REQUIREMENT SOURCES, MERGE POLICY (focal point),
// NOTIFICATION RECIPIENTS, CONFIGURED RUN BUDGET, GITHUB CHECK PREVIEW
import { useState } from 'react'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import styles from './SetupVerification.module.css'

const PREVIEW_STATES = [
  { value: 'preparing',   label: 'Preparing requirements',          pill: 'idle' },
  { value: 'ready',       label: 'Requirements ready for review',   pill: 'info' },
  { value: 'in_progress', label: 'Verification in progress',        pill: 'info' },
  { value: 'complete',    label: 'Verification complete',           pill: 'ok'   },
  { value: 'incomplete',  label: 'Verification incomplete',         pill: 'bad'  },
  { value: 'no_reqs',     label: 'No requirements found',           pill: 'warn' },
]

const PREVIEW_DETAIL = {
  preparing:   { heading: 'Preparing Requirements', body: 'Intent Gate is reading the ticket and extracting acceptance criteria. This usually takes under 30 seconds.', action: null },
  ready:       { heading: 'Requirements Ready for Review', body: 'Intent Gate has extracted 7 acceptance criteria. Review and confirm them before starting verification.', action: 'CONFIRM REQUIREMENTS ›' },
  in_progress: { heading: 'Verification in Progress', body: '4 of 7 requirements have been verified. Workers are read-only and cannot edit code or execute repository commands.', action: 'VIEW PROGRESS ›' },
  complete:    { heading: 'Verification Complete', body: 'All 7 requirements have been verified. Review the gate decision and evidence before merging.', action: 'VIEW RESULTS ›' },
  incomplete:  { heading: 'Verification Incomplete', body: 'Verification could not be completed for all requirements. The gate is blocked by default. Review what was and was not verified.', action: 'VIEW RECORD ›' },
  no_reqs:     { heading: 'No Requirements Found', body: 'Intent Gate could not extract acceptance criteria from the linked ticket. Check that the PR description links to a valid ticket.', action: null },
}

export default function SetupVerification() {
  const [connected, setConnected] = useState(true)
  const [policy, setPolicy] = useState('block')
  const [previewState, setPreviewState] = useState('ready')
  const [sources, setSources] = useState({ jira: true, confluence: false, github_issues: false })
  const [budget, setBudget] = useState('12.00')
  const [recipients, setRecipients] = useState('aj@user.dev')
  const [saved, setSaved] = useState(false)

  function handleSave(e) {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const detail = PREVIEW_DETAIL[previewState]
  const previewPill = PREVIEW_STATES.find(s => s.value === previewState)

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Repository Settings</h1>
      </div>

      <form onSubmit={handleSave} noValidate>
        {/* ── CONNECT GITHUB ─────────────────────────────────────── */}
        <section className={styles.card}>
          <h2 className="micro-label">Connect GitHub</h2>
          {connected ? (
            <div className={styles.connectedRow}>
              <div className={styles.fieldGrid}>
                <div className={styles.field}>
                  <label className={styles.fieldLabel} htmlFor="org">Organization</label>
                  <select id="org" className={styles.select}>
                    <option>egoys</option>
                    <option>user</option>
                  </select>
                </div>
                <div className={styles.field}>
                  <label className={styles.fieldLabel} htmlFor="repo">Repository</label>
                  <select id="repo" className={styles.select}>
                    <option>user/payments-api</option>
                    <option>user/identity-service</option>
                  </select>
                </div>
              </div>
              <Badge variant="ok">Connected</Badge>
            </div>
          ) : (
            <div className={styles.disconnectedRow}>
              <p className={styles.helpText}>Connect your GitHub account to enable automated verification on pull requests.</p>
              <Button variant="primary" type="button" onClick={() => setConnected(true)}>
                CONNECT GITHUB ›
              </Button>
            </div>
          )}
        </section>

        {/* ── REQUIREMENT SOURCES ────────────────────────────────── */}
        <section className={styles.card}>
          <h2 className="micro-label">Requirement Sources</h2>
          <div className={styles.checkboxGroup}>
            {[
              { id: 'jira',          label: 'Jira',           desc: 'Link tickets via PR description.' },
              { id: 'confluence',    label: 'Confluence',     desc: 'Fetch spec pages linked in the ticket.' },
              { id: 'github_issues', label: 'GitHub Issues',  desc: 'Use GitHub Issues as the ticket source.' },
            ].map(src => (
              <label key={src.id} className={`${styles.checkCard} ${sources[src.id] ? styles.checkCardActive : ''}`}>
                <input
                  type="checkbox"
                  className={styles.checkbox}
                  checked={sources[src.id]}
                  onChange={e => setSources(s => ({ ...s, [src.id]: e.target.checked }))}
                />
                <div>
                  <span className={styles.checkLabel}>{src.label}</span>
                  <span className={styles.checkDesc}>{src.desc}</span>
                </div>
              </label>
            ))}
          </div>
          {Object.values(sources).some(Boolean) && (
            <div className={styles.sunken}>
              <span className="micro-label">Selected Documents</span>
              <ul className={styles.selectedList}>
                {sources.jira          && <li>Jira — linked ticket</li>}
                {sources.confluence    && <li>Confluence — linked spec page</li>}
                {sources.github_issues && <li>GitHub Issues — linked issue</li>}
              </ul>
            </div>
          )}
        </section>

        {/* ── MERGE POLICY ───────────────────────────────────────── */}
        <section className={styles.card}>
          <h2 className="micro-label">Merge Policy</h2>
          <p className={styles.sectionHint}>Controls what happens when Intent Gate emits a non-passing verdict.</p>
          <div className={styles.radioGroup} role="radiogroup" aria-label="Merge policy">
            {[
              {
                value: 'block',
                label: 'BLOCK MERGE',
                desc: 'A non-certified run sets exit_code=1 and blocks the PR. This is the default and recommended setting.',
                pill: 'bad',
              },
              {
                value: 'warn',
                label: 'WARN ONLY',
                desc: 'The check reports a warning but does not block the merge. The gate decision is advisory.',
                pill: 'warn',
              },
              {
                value: 'record',
                label: 'RECORD ONLY',
                desc: 'Results are logged to the Verification Record but the PR is never blocked.',
                pill: 'idle',
              },
            ].map(opt => (
              <label
                key={opt.value}
                className={`${styles.radioCard} ${policy === opt.value ? styles.radioCardSelected : ''}`}
              >
                <input
                  type="radio"
                  name="merge_policy"
                  value={opt.value}
                  checked={policy === opt.value}
                  onChange={() => setPolicy(opt.value)}
                  className={styles.radioInput}
                />
                <div className={styles.radioContent}>
                  <div className={styles.radioTop}>
                    <span className="micro-label">{opt.label}</span>
                    <Badge variant={opt.pill}>{opt.label}</Badge>
                  </div>
                  <p className={styles.radioDesc}>{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* ── NOTIFICATION RECIPIENTS ────────────────────────────── */}
        <section className={styles.card}>
          <h2 className="micro-label">Notification Recipients</h2>
          <div className={styles.field}>
            <label className={styles.fieldLabel} htmlFor="recipients">
              Email addresses (comma-separated)
            </label>
            <input
              id="recipients"
              type="text"
              className={styles.input}
              value={recipients}
              onChange={e => setRecipients(e.target.value)}
              placeholder="team@example.com"
            />
          </div>
        </section>

        {/* ── CONFIGURED RUN BUDGET ──────────────────────────────── */}
        <section className={styles.card}>
          <h2 className="micro-label">Configured Run Budget</h2>
          <div className={styles.field}>
            <label className={styles.fieldLabel} htmlFor="budget">
              Maximum simulated spend per run
            </label>
            <div className={styles.inputRow}>
              <input
                id="budget"
                type="number"
                min="0"
                step="0.01"
                className={`${styles.input} ${styles.inputNarrow}`}
                value={budget}
                onChange={e => setBudget(e.target.value)}
              />
              <span className={styles.inputSuffix}>USD / run</span>
            </div>
          </div>
        </section>

        {/* ── FOOTER ACTIONS ─────────────────────────────────────── */}
        <div className={styles.formFooter}>
          <Button variant="secondary" type="button">CANCEL</Button>
          <Button variant="primary" type="submit" disabled={saved}>
            {saved ? 'SAVED ✓' : 'SAVE SETTINGS'}
          </Button>
        </div>
      </form>

      {/* ── GITHUB CHECK PREVIEW ───────────────────────────────────── */}
      <section className={styles.card} style={{ marginTop: 0 }}>
        <div className={styles.previewHeader}>
          <h2 className="micro-label">GitHub Check Preview</h2>
          <div className={styles.field} style={{ minWidth: 280 }}>
            <label className={styles.fieldLabel} htmlFor="preview-state">Preview state</label>
            <select
              id="preview-state"
              className={styles.select}
              value={previewState}
              onChange={e => setPreviewState(e.target.value)}
            >
              {PREVIEW_STATES.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className={styles.previewCard}>
          <div className={styles.previewTop}>
            {/* GitHub check icon */}
            <span className={styles.previewIcon} aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
              </svg>
            </span>
            <div className={styles.previewMeta}>
              <span className={styles.previewTitle}>intent-gate / verify</span>
              <span className={styles.previewSub}>Intent Attestation Gate</span>
            </div>
            <Badge variant={previewPill?.pill ?? 'idle'}>{previewPill?.label}</Badge>
          </div>

          <div className={styles.previewBody}>
            <p className={styles.previewHeading}>{detail.heading}</p>
            <p className={styles.previewText}>{detail.body}</p>
            {detail.action && (
              <span className={styles.previewAction}>{detail.action}</span>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
