// src/components/TopBar.jsx
import styles from './TopBar.module.css'

export default function TopBar({ onMenu, navOpen = false }) {
  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        {/* Drawer toggle — only visible below 1024px */}
        <button
          type="button"
          className={styles.menuBtn}
          onClick={onMenu}
          aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
          aria-expanded={navOpen}
          aria-controls="sidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
          </svg>
        </button>

        {/* Branch glyph + repository selector */}
        <span className={styles.branchIcon} aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--violet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="6" y1="3" x2="6" y2="15"/>
            <circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="6" cy="6" r="3"/>
            <path d="M18 9a9 9 0 0 1-9 9"/>
          </svg>
        </span>
        <div className={styles.repoBlock}>
          <span className="micro-label">Repository</span>
          <select className={styles.repoSelect} aria-label="Select repository">
            <option>user/payments-api</option>
            <option>user/identity-service</option>
          </select>
        </div>
      </div>

      <div className={styles.right}>
        <div className={styles.avatar} aria-label="User avatar" role="img">AJ</div>
        <div className={styles.userInfo}>
          <span className={styles.userName}>Demo User</span>
          <span className={styles.userEmail}>aj@user.dev · Demo user</span>
        </div>
      </div>
    </header>
  )
}
