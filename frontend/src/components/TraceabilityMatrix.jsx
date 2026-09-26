export default function TraceabilityMatrix({ verdicts = [] }) {
  return (
    <section>
      <h2>Traceability matrix</h2>
      <table border="1" cellPadding="6">
        <thead><tr><th>Criterion</th><th>Verdict</th><th>Tier</th><th>Locations</th></tr></thead>
        <tbody>
          {verdicts.map((v) => (
            <tr key={v.criterion_id}>
              <td>{v.criterion_id}</td><td>{v.verdict}</td><td>{v.evidence_tier}</td>
              <td>{(v.locations || []).join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
