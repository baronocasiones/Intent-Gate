// src/components/Modal.jsx — S6 Override modal
// Focus-trapped, closes on Escape, confirms disabled under 20 chars
import { useEffect, useRef, useState } from 'react'
import Button from './Button.jsx'
import styles from './Modal.module.css'

const MIN_CHARS = 20

export default function Modal({ open, onClose }) {
  const [reason, setReason] = useState('')
  const [recipients, setRecipients] = useState('aj@user.dev')
  const panelRef = useRef(null)
  const canSubmit = reason.length >= MIN_CHARS

  // Focus trap + Escape
  useEffect(() => {
    if (!open) return
    const el = panelRef.current
    if (!el) return
    const focusable = Array.from(
      el.querySelectorAll('button,[href],input,textarea,[tabindex]:not([tabindex="-1"])')
    )
    focusable[0]?.focus()

    function onKey(e) {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key !== 'Tab') return
      const first = focusable[0]
      const last  = focusable[focusable.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last?.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first?.focus() }
      }
    }
    document.addEventListener('keydown', onKey)
    // Background must not scroll while the dialog is open
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className={styles.backdrop} onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div
        className={styles.panel}
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <h2 id="modal-title" className={styles.title}>OVERRIDE MERGE GATE?</h2>
        <p className={styles.subtitle}>
          <em>This action will be logged and is auditable. Proceed only if you have reviewed the evidence.</em>
        </p>

        {/* Summary */}
        <div className={styles.summary}>
          <div className={styles.summaryRow}>
            <span className="micro-label">Pull Request</span>
            <span>#482 — Enforce supervisor approval on refunds</span>
          </div>
          <div className={styles.summaryRow}>
            <span className="micro-label">Commit</span>
            <code className={styles.mono}>a3f9c12</code>
          </div>
          <div className={styles.summaryRow}>
            <span className="micro-label">Affected Findings</span>
            <span>AC-2 — Rejected</span>
          </div>
          <div className={styles.summaryRow}>
            <span className="micro-label">Current User</span>
            <span>aj@user.dev</span>
          </div>
        </div>

        {/* Reason */}
        <div className={styles.field}>
          <label className={styles.fieldLabel} htmlFor="override-reason">
            REASON FOR OVERRIDE
          </label>
          <textarea
            id="override-reason"
            className={styles.textarea}
            value={reason}
            onChange={e => setReason(e.target.value)}
            rows={4}
            placeholder="Describe why the merge gate is being overridden…"
            aria-describedby="reason-counter reason-warn"
          />
          <div className={styles.reasonMeta}>
            <span id="reason-counter" className={styles.counter}>
              {reason.length}/{MIN_CHARS} Minimum Characters
            </span>
            {!canSubmit && reason.length > 0 && (
              <span id="reason-warn" className={styles.warnText} role="alert">
                {MIN_CHARS - reason.length} more character{MIN_CHARS - reason.length !== 1 ? 's' : ''} required.
              </span>
            )}
          </div>
        </div>

        {/* Recipients */}
        <div className={styles.field}>
          <label className={styles.fieldLabel} htmlFor="override-recipients">
            NOTIFICATION RECIPIENTS
          </label>
          <input
            id="override-recipients"
            type="text"
            name="recipients"
            className={styles.input}
            value={recipients}
            onChange={e => setRecipients(e.target.value)}
            autoComplete="off"
            spellCheck={false}
            inputMode="email"
          />
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          <Button variant="secondary" onClick={onClose}>CANCEL</Button>
          <Button variant="danger" disabled={!canSubmit} onClick={onClose}>
            CONFIRM OVERRIDE
          </Button>
        </div>
      </div>
    </div>
  )
}
