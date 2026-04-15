import type { PropsWithChildren } from 'react'

export function Page({ title, subtitle, children }: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <section>
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </header>
      {children}
    </section>
  )
}

export function Card({ title, children }: PropsWithChildren<{ title: string }>) {
  return (
    <article className="card">
      <h3>{title}</h3>
      {children}
    </article>
  )
}

export function MiniLineChart({ points, height = 140 }: { points: number[]; height?: number }) {
  if (!points.length) return <p>No chart data yet.</p>
  const min = Math.min(...points)
  const max = Math.max(...points)
  const width = 420
  const span = max - min || 1
  const coords = points.map((point, index) => {
    const x = (index / Math.max(points.length - 1, 1)) * width
    const y = height - ((point - min) / span) * (height - 16) - 8
    return `${x},${y}`
  }).join(' ')
  return (
    <div className="chart-box">
      <svg viewBox={`0 0 ${width} ${height}`} className="mini-chart" preserveAspectRatio="none">
        <polyline fill="none" stroke="currentColor" strokeWidth="3" points={coords} />
      </svg>
      <div className="chart-labels">
        <span>{min.toFixed(2)}</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  )
}
