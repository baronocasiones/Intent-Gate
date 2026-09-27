// The API serves M9's lowercase D9 vocabulary (certified / conditional /
// rejected / pending). This badge used to compare uppercase literals, so every
// real outcome fell through to the undecided orange and a rejected run looked
// undecided. CONDITIONAL had no branch at all. architecture.md §11.19.
const COLORS = {
  CERTIFIED: 'green',
  CONDITIONAL: 'orange',
  REJECTED: 'red',
  PENDING: 'orange',
}

export default function VerdictBadge({ verdict }) {
  const label = String(verdict || '').toUpperCase() || 'UNKNOWN'
  const color = COLORS[label] || 'orange'
  return <span style={{ background: color, color: 'white', padding: '4px 12px', borderRadius: 12 }}>{label}</span>
}
