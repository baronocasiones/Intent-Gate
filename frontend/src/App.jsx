// src/App.jsx — shell: sidebar + topbar + router outlet + data-source banner
import { useEffect, useState } from 'react'
import './styles/tokens.css'
import { useHashRouter, matchRoute } from './router.js'
import { getRun } from './data/index.js'
import Sidebar from './components/Sidebar.jsx'
import TopBar from './components/TopBar.jsx'
import DataSourceBanner from './components/DataSourceBanner.jsx'
import RunsList from './screens/RunsList.jsx'
import SetupVerification from './screens/SetupVerification.jsx'
import ConfirmRequirements from './screens/ConfirmRequirements.jsx'
import Verifying from './screens/Verifying.jsx'
import RunDetail from './screens/RunDetail.jsx'
import Record from './screens/Record.jsx'
import Exposure from './screens/Exposure.jsx'
import AuditHistory from './screens/AuditHistory.jsx'
import styles from './App.module.css'

// Smart run screen — shows Verifying when running, RunDetail otherwise
function RunScreen({ runId }) {
  const [status, setStatus] = useState(null)
  useEffect(() => {
    getRun(runId).then(r => setStatus(r?.status ?? null))
  }, [runId])
  if (status === null) return null
  return status === 'running'
    ? <Verifying runId={runId} />
    : <RunDetail runId={runId} />
}

// Route table — more-specific patterns first
const ROUTES = [
  { pattern: '/runs/:id/confirm', component: (p) => <ConfirmRequirements runId={p.id} /> },
  { pattern: '/runs/:id/record',  component: (p) => <Record runId={p.id} /> },
  { pattern: '/runs/:id',         component: (p) => <RunScreen runId={p.id} /> },
  { pattern: '/runs',             component: () => <RunsList /> },
  { pattern: '/setup',            component: () => <SetupVerification /> },
  { pattern: '/exposure',         component: () => <Exposure /> },
  { pattern: '/audit',            component: () => <AuditHistory /> },
  { pattern: '/',                 component: () => <RunsList /> },
]

function resolveScreen(path) {
  for (const route of ROUTES) {
    const params = matchRoute(route.pattern, path)
    if (params !== null) return route.component(params)
  }
  return <RunsList />
}

export default function App() {
  const [path, navigate] = useHashRouter()
  const [navOpen, setNavOpen] = useState(false)
  const screen = resolveScreen(path)

  // Close the mobile drawer whenever the route changes
  useEffect(() => { setNavOpen(false) }, [path])

  // ESC closes the drawer
  useEffect(() => {
    if (!navOpen) return
    const onKey = e => { if (e.key === 'Escape') setNavOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navOpen])

  return (
    <div className={styles.shell}>
      {/* Skip link — must not touch location.hash (the hash IS the router) */}
      <a
        href="#main"
        className={styles.skipLink}
        onClick={e => { e.preventDefault(); document.getElementById('main')?.focus() }}
      >
        Skip to main content
      </a>
      <Sidebar currentPath={path} open={navOpen} onClose={() => setNavOpen(false)} />
      {navOpen && (
        <div className={styles.scrim} onClick={() => setNavOpen(false)} aria-hidden="true" />
      )}
      <div className={styles.main}>
        <DataSourceBanner />
        <TopBar onMenu={() => setNavOpen(o => !o)} navOpen={navOpen} />
        <main id="main" tabIndex={-1} className={styles.content}>
          {screen}
        </main>
      </div>
    </div>
  )
}
