// src/components/Sidebar.jsx
import { useEffect, useRef } from 'react'
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  {
    id: 'runs',
    label: 'Verification Runs',
    route: '/runs',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    id: 'setup',
    label: 'Repository Settings',
    route: '/setup',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
      </svg>
    ),
  },
  {
    id: 'exposure',
    label: 'Exposure',
    route: '/exposure',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
  },
  {
    id: 'audit',
    label: 'Audit History',
    route: '/audit',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
]

export default function Sidebar({ currentPath, open = false, onClose }) {
  const ref = useRef(null)

  // Drawer opened → move focus inside; closed again → hand focus back
  useEffect(() => {
    if (open && ref.current) {
      const first = ref.current.querySelector('a, button')
      first?.focus()
    }
  }, [open])

  function isActive(route) {
    if (route === '/runs') return currentPath === '/runs' || currentPath === '/' || currentPath.startsWith('/runs/')
    return currentPath.startsWith(route)
  }

  return (
    <aside
      id="sidebar"
      ref={ref}
      className={`${styles.sidebar} ${open ? styles.sidebarOpen : ''}`}
    >
      {/* Brand block */}
      <div className={styles.brand}>
        <div className={styles.logoMark} aria-hidden="true">
          <svg width="32" height="32" viewBox="0 0 36 36" fill="none">
            <polygon points="18,2 34,10 34,26 18,34 2,26 2,10" fill="var(--violet)" />
            <polygon points="18,8 28,13 28,23 18,28 8,23 8,13" fill="none" stroke="white" strokeWidth="1.5" />
            <line x1="18" y1="8" x2="18" y2="28" stroke="white" strokeWidth="1.5" />
          </svg>
        </div>
        <div className={styles.brandText}>
          <span className={styles.brandName}>Intent Gate</span>
          <span className={styles.brandSub}>Attestation Workspace</span>
        </div>
        <button
          type="button"
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="Close navigation"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
            <line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" />
          </svg>
        </button>
      </div>

      {/* Nav */}
      <nav className={styles.nav} aria-label="Main navigation">
        <span className={styles.navLabel}>Workspace</span>
        <ul className={styles.navList} role="list">
          {NAV_ITEMS.map(item => {
            const active = isActive(item.route)
            return (
              <li key={item.id}>
                {/* Real hash link — no preventDefault, so Cmd/Ctrl/middle-click and
                    deep links keep working; the hash router reacts to hashchange. */}
                <a
                  href={`#${item.route}`}
                  className={`${styles.navItem} ${active ? styles.navItemActive : ''}`}
                  aria-current={active ? 'page' : undefined}
                >
                  <span className={styles.navIcon}>{item.icon}</span>
                  <span>{item.label}</span>
                </a>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <footer className={styles.footer}>
        <span>© 2026. Egoys. All Rights Reserved.</span>
      </footer>
    </aside>
  )
}
