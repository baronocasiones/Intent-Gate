// src/components/Badge.jsx — semantic pill / badge
import styles from './Badge.module.css'

/**
 * variant: 'ok' | 'bad' | 'warn' | 'info' | 'idle'
 */
export default function Badge({ children, variant = 'idle', className = '' }) {
  return (
    <span className={`${styles.badge} ${styles[variant]} ${className}`}>
      {children}
    </span>
  )
}
