import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, MiniLineChart, Page } from '../components'
import { formatMapKey } from '../format'
import type { AnalyticsOverview } from '../types'

function renderMap(map: Record<string, number>) {
  const items = Object.entries(map)
  if (items.length === 0) return <p>Данных пока нет.</p>
  return (
    <ul>
      {items.map(([key, value]) => (
        <li key={key}>{formatMapKey(key)}: {typeof value === 'number' ? value.toFixed(4) : value}</li>
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
    <Page title="Аналитика" subtitle="Расширенная торговая аналитика с учётом жизненного цикла сделок, серий и соблюдения стратегии.">
      <div className="card-grid four-columns">
        <Card title="Сделки"><strong>{analytics?.total_trades ?? 0}</strong></Card>
        <Card title="Закрыто"><strong>{analytics?.closed_trades ?? 0}</strong></Card>
        <Card title="Profit Factor"><strong>{analytics?.profit_factor?.toFixed(4) ?? '0.0000'}</strong></Card>
        <Card title="Средний R/R"><strong>{analytics?.average_rr?.toFixed(4) ?? '0.0000'}</strong></Card>
      </div>
      <div className="card-grid four-columns">
        <Card title="Максимальная просадка"><strong>{analytics?.max_drawdown?.toFixed(2) ?? '0.00'}%</strong></Card>
        <Card title="Среднее удержание"><strong>{analytics?.average_hold_minutes?.toFixed(2) ?? '0.00'} мин</strong></Card>
        <Card title="Среднее соблюдение"><strong>{analytics?.average_compliance_score?.toFixed(2) ?? '0.00'}</strong></Card>
        <Card title="Серии"><strong>W {analytics?.streaks?.max_win_streak ?? 0} / L {analytics?.streaks?.max_loss_streak ?? 0}</strong></Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="По режиму">{renderMap(analytics?.by_mode ?? {})}</Card>
        <Card title="По рынку">{renderMap(analytics?.by_market ?? {})}</Card>
        <Card title="По инструменту">{renderMap(analytics?.by_symbol ?? {})}</Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="По направлению">{renderMap(analytics?.by_direction ?? {})}</Card>
        <Card title="По причине закрытия">{renderMap(analytics?.by_close_reason ?? {})}</Card>
        <Card title="Распределение TP">{renderMap(analytics?.tp_hit_distribution ?? {})}</Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="PnL по месяцам">{renderMap(analytics?.monthly_pnl ?? {})}</Card>
        <Card title="PnL по годам">{renderMap(analytics?.yearly_pnl ?? {})}</Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="По дням недели">{renderMap(analytics?.by_weekday ?? {})}</Card>
        <Card title="По часам">{renderMap(analytics?.by_hour ?? {})}</Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Кривая капитала">
          <MiniLineChart points={analytics?.recent_equity_curve ?? []} />
        </Card>
      </div>
    </Page>
  )
}
