import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, MiniLineChart, Page } from '../components'
import type { AnalyticsOverview } from '../types'

function renderMap(map: Record<string, number>) {
  const items = Object.entries(map)
  if (items.length === 0) return <p>No data yet.</p>
  return (
    <ul>
      {items.map(([key, value]) => (
        <li key={key}>{key}: {typeof value === 'number' ? value.toFixed(4) : value}</li>
      ))}
    </ul>
  )
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null)

  useEffect(() => {
    api.getAnalytics().then(setAnalytics).catch(() => setAnalytics(null))
  }, [])

  return (
    <Page title="Analytics" subtitle="Extended trading analytics with lifecycle-aware buckets, streaks and compliance tracking.">
      <div className="card-grid four-columns">
        <Card title="Trades"><strong>{analytics?.total_trades ?? 0}</strong></Card>
        <Card title="Closed"><strong>{analytics?.closed_trades ?? 0}</strong></Card>
        <Card title="Profit factor"><strong>{analytics?.profit_factor?.toFixed(4) ?? '0.0000'}</strong></Card>
        <Card title="Average R/R"><strong>{analytics?.average_rr?.toFixed(4) ?? '0.0000'}</strong></Card>
      </div>
      <div className="card-grid four-columns">
        <Card title="Max drawdown"><strong>{analytics?.max_drawdown?.toFixed(2) ?? '0.00'}%</strong></Card>
        <Card title="Avg hold"><strong>{analytics?.average_hold_minutes?.toFixed(2) ?? '0.00'}m</strong></Card>
        <Card title="Avg compliance"><strong>{analytics?.average_compliance_score?.toFixed(2) ?? '0.00'}</strong></Card>
        <Card title="Streaks"><strong>W {analytics?.streaks?.max_win_streak ?? 0} / L {analytics?.streaks?.max_loss_streak ?? 0}</strong></Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="By mode">{renderMap(analytics?.by_mode ?? {})}</Card>
        <Card title="By market">{renderMap(analytics?.by_market ?? {})}</Card>
        <Card title="By symbol">{renderMap(analytics?.by_symbol ?? {})}</Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="By direction">{renderMap(analytics?.by_direction ?? {})}</Card>
        <Card title="By close reason">{renderMap(analytics?.by_close_reason ?? {})}</Card>
        <Card title="TP distribution">{renderMap(analytics?.tp_hit_distribution ?? {})}</Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Monthly PnL">{renderMap(analytics?.monthly_pnl ?? {})}</Card>
        <Card title="Yearly PnL">{renderMap(analytics?.yearly_pnl ?? {})}</Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="By weekday">{renderMap(analytics?.by_weekday ?? {})}</Card>
        <Card title="By hour">{renderMap(analytics?.by_hour ?? {})}</Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Equity curve preview">
          <MiniLineChart points={analytics?.recent_equity_curve ?? []} />
        </Card>
      </div>
    </Page>
  )
}
