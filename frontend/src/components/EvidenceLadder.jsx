const TIERS = ['E0', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6']

export default function EvidenceLadder({ verdicts = [] }) {
  return (
    <section>
      <h2>Evidence ladder (E0–E6)</h2>
      <ul>{TIERS.map((t) => <li key={t}>{t}: {verdicts.filter((v) => v.evidence_tier === t).length} criteria</li>)}</ul>
    </section>
  )
}
