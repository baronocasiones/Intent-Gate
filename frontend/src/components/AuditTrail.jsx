// The audit trail (Convention 5): per criterion, the verdict, the evidence tier
// it was reached at, and the reason. This text is what the gate exists to
// produce — it was in every fixture and served by the API, and rendered
// nowhere. Locations are not repeated here; the traceability matrix above owns
// them, and the rationale prose cites them itself.
export default function AuditTrail({ verdicts = [] }) {
  return (
    <section>
      <h2>Audit trail</h2>
      {verdicts.length === 0 ? <p>No criteria were extracted from this requirement.</p> : (
        <ul>
          {verdicts.map((v) => (
            <li key={v.criterion_id}>
              <strong>{v.criterion_id} — {v.verdict} @ {v.evidence_tier}</strong>
              <div>{v.rationale}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
