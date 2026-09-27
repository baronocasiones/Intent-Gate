// src/components/DataSourceBanner.jsx — §3.7.2
// Persistent banner on every route. In Phase A always shows "STATIC PREVIEW".
// In Phase B getSource() returns 'live' or 'fallback' and the message changes.
import { useEffect, useState } from 'react'
import { getSource } from '../data/index.js'
import styles from './DataSourceBanner.module.css'

const MESSAGES = {
  static:   'STATIC PREVIEW · backend API not final',
  fallback: 'FIXTURE MODE · API unavailable — showing cached data',
  live:     null, // live mode: banner hidden
}

export default function DataSourceBanner() {
  const [source, setSource] = useState('static')

  useEffect(() => {
    getSource().then(setSource)
  }, [])

  const msg = MESSAGES[source]
  if (!msg) return null

  return (
    <div
      className={`${styles.banner} ${styles[source]}`}
      role="status"
      aria-live="polite"
    >
      <span className={styles.label}>{msg}</span>
    </div>
  )
}
