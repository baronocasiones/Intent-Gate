// Fixture fallback — mirrors fixtures/demo_run.json until live backend lands.
export default {
  run_id: 'demo',
  status: 'PENDING',
  measured: false,
  verdicts: [
    { criterion_id: 'AC-1', verdict: 'PENDING', evidence_tier: 'E0', locations: [], rationale: 'stub' },
  ],
}
