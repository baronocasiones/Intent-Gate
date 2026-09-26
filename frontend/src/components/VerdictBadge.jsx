export default function VerdictBadge({ verdict }) {
  const color = verdict === 'CERTIFIED' ? 'green' : verdict === 'REJECTED' ? 'red' : 'orange'
  return <span style={{ background: color, color: 'white', padding: '4px 12px', borderRadius: 12 }}>{verdict}</span>
}
