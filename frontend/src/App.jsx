import { useEffect, useState } from 'react'
import { fetchRun, fetchRunList } from './api.js'
import VerdictBadge from './components/VerdictBadge.jsx'
import TraceabilityMatrix from './components/TraceabilityMatrix.jsx'
import EvidenceLadder from './components/EvidenceLadder.jsx'
import AuditTrail from './components/AuditTrail.jsx'

// The fallback is the canonical fixture served out of public/ — the same bytes
// the backend tests byte-pin against fixtures/demo_run.json. It used to be a
// third hand-written copy holding one AC-1 PENDING@E0 row, which meant a failed
// live call silently showed a *weaker* result rather than the same one
// (M2 request 1).
const FIXTURE_RUN_URL = '/fixtures/demo_run.json'

// An explicit ?run_id= wins, so the demo can point at one exact run. Otherwise
// take the newest run the index reports — a hardcoded id 404s, which is what
// pinned this component to its fixture forever (architecture.md §11.19).
async function loadRun(requestedId) {
  try {
    if (requestedId) {
      const run = await fetchRun(requestedId)
      if (run) return { run, live: true }
    }
    const runs = await fetchRunList()
    if (runs && runs.length) {
      const run = await fetchRun(runs[0].run_id)
      if (run) return { run, live: true }
    }
  } catch (err) {
    // A refused connection or a dropped socket lands here, not the `!res.ok`
    // path. The fallback has to live in here: when it lived in the caller's
    // `.catch()` the screen stranded on a spinner instead, because the fetch
    // never resolves. Convention 4 — the live call is never something the demo
    // depends on.
  }
  const res = await fetch(FIXTURE_RUN_URL)
  if (!res.ok) return { run: null, live: false }
  return { run: await res.json(), live: false }
}

export default function App() {
  const [run, setRun] = useState(null)
  const [live, setLive] = useState(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get('run_id')
    loadRun(requested)
      .then((result) => {
        if (result.run) { setRun(result.run); setLive(result.live) } else setFailed(true)
      })
      .catch(() => setFailed(true))
  }, [])

  return (
    <main style={{ fontFamily: 'system-ui', padding: 24, maxWidth: 960 }}>
      <h1>
        Intent Attestation Gate{' '}
        {run ? <small>{run.run_id}{live ? '' : ' · fixture mode'}</small> : null}
      </h1>
      {/* Nothing is rendered below until a run is in hand: a bare evidence
          ladder and an empty matrix would assert "no criteria were found",
          which is a claim about the requirement rather than about us failing
          to load one. */}
      {!run ? <p><small>{failed ? 'No run available and the fallback fixture could not be loaded.' : 'Loading…'}</small></p> : (
        <>
          <VerdictBadge verdict={run.status} />
          <EvidenceLadder verdicts={run.verdicts} />
          <TraceabilityMatrix verdicts={run.verdicts} />
          <AuditTrail verdicts={run.verdicts} />
        </>
      )}
    </main>
  )
}
