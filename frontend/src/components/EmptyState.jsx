// src/components/EmptyState.jsx
import styles from './EmptyState.module.css'

export default function EmptyState({ title = 'Nothing here', message }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.icon} aria-hidden="true">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <p className={styles.title}>{title}</p>
      {message && <p className={styles.message}>{message}</p>}
    </div>
  )
}
