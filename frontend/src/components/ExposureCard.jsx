export default function ExposureCard({ metrics }) {
  return (
    <section>
      <h2>Risk-weighted exposure</h2>
      <p>false_certified_rate: {metrics.false_certified_rate ?? 'unmeasured'} {metrics.measured ? '(measured)' : '(fixture)'}</p>
    </section>
  )
}
