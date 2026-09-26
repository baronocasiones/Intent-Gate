import { useEffect, useState } from 'react'
import { fetchRun, fetchMetrics } from './api.js'
import demoRun from './fixtures.js'
import VerdictBadge from './components/VerdictBadge.jsx'
import TraceabilityMatrix from './components/TraceabilityMatrix.jsx'
import EvidenceLadder from './components/EvidenceLadder.jsx'
import ExposureCard from './components/ExposureCard.jsx'

export default function App() {
  const [run, setRun] = useState(demoRun)
  const [metrics, setMetrics] = useState({ false_certified_rate: null, measured: false })
  const [live, setLive] = useState(false)

  useEffect(() => {
    // Live-API first, fixture fallback so demo never dies on a failed call.
    fetchRun('demo').then((r) => { if (r) { setRun(r); setLive(true) } }).catch(() => {})
    fetchMetrics().then((m) => { if (m) setMetrics(m) }).catch(() => {})
  }, [])

  return (
    <main style={{ fontFamily: 'system-ui', padding: 24, maxWidth: 960 }}>
      <h1>Intent Attestation Gate {!live && <small>(fixture mode)</small>}</h1>
      <VerdictBadge verdict={run.status} />
      <EvidenceLadder verdicts={run.verdicts} />
      <TraceabilityMatrix verdicts={run.verdicts} />
      <ExposureCard metrics={metrics} />
    </main>
  )
}
