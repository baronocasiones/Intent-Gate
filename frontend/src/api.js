// Live API with graceful null on failure — caller falls back to fixtures.
export async function fetchRun(runId) {
  const res = await fetch(`/api/runs/${runId}`)
  if (!res.ok) return null
  return res.json()
}

export async function fetchMetrics() {
  const res = await fetch('/api/metrics')
  if (!res.ok) return null
  return res.json()
}
