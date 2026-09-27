// Live API with graceful null on failure — caller falls back to fixtures.
export async function fetchRun(runId) {
  const res = await fetch(`/api/runs/${runId}`)
  if (!res.ok) return null
  return res.json()
}

// The run index, newest first (M15). This is how the dashboard discovers a run
// id that can exist: the detail route 404s an unknown id, so a page opened
// without an explicit `?run_id=` has to ask the server what it has. An empty
// index (fresh database) is a legitimate answer, not an error — the caller
// falls back to the fixture. architecture.md §11.19.
export async function fetchRunList() {
  const res = await fetch('/api/runs')
  if (!res.ok) return null
  const body = await res.json()
  return body.runs || []
}
