import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, MiniLineChart, Page } from '../components'
import { formatDateTime, onOff, t, yesNo } from '../format'
import type { AnalyticsOverview, BacktestRun, BalanceOverview, BotConfig, PnlOverview, ReleaseReadiness, RuntimeSettings, StrategyDecision, SystemState } from '../types'

export default function DashboardPage() {
  const [health, setHealth] = useState<string>('загрузка')
  const [settings, setSettings] = useState<RuntimeSettings | null>(null)
  const [balances, setBalances] = useState<BalanceOverview | null>(null)
  const [pnl, setPnl] = useState<PnlOverview | null>(null)
  const [decisions, setDecisions] = useState<StrategyDecision[]>([])
  const [runs, setRuns] = useState<BacktestRun[]>([])
  const [bot, setBot] = useState<BotConfig | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null)
  const [ops, setOps] = useState<SystemState | null>(null)
  const [readiness, setReadiness] = useState<ReleaseReadiness | null>(null)

  useEffect(() => {
    api.health().then((data) => setHealth(`${data.status} · ${data.service}`)).catch(() => setHealth('недоступно'))
    api.getSettings().then(setSettings).catch(() => setSettings(null))
    api.getBalances().then(setBalances).catch(() => setBalances(null))
    api.getPnl().then(setPnl).catch(() => setPnl(null))
    api.getStrategyDecisions().then((data) => setDecisions(data.slice(0, 5))).catch(() => setDecisions([]))
    api.getBacktestRuns().then((data) => setRuns(data.slice(0, 3))).catch(() => setRuns([]))
    api.getBotConfig().then(setBot).catch(() => setBot(null))
    api.getAnalytics().then(setAnalytics).catch(() => setAnalytics(null))
    api.getOpsState().then(setOps).catch(() => setOps(null))
    api.getReleaseReadiness().then(setReadiness).catch(() => setReadiness(null))
  }, [])

  return (
    <Page title="Панель управления" subtitle="Операционная сводка по режиму, балансам, решениям стратегии, состоянию бота и безопасности production-контура.">
      <div className="card-grid four-columns">
        <Card title="Состояние API"><strong>{health}</strong></Card>
        <Card title="Режим работы">
          <strong>{settings ? t(settings.mode) : '—'}</strong>
          <p>Спот: {onOff(settings?.spot_enabled)}</p>
          <p>Фьючерсы: {onOff(settings?.futures_enabled)}</p>
        </Card>
        <Card title="Баланс">
          <strong>${balances?.total_wallet_usd?.toFixed(2) ?? '0.00'}</strong>
          <p>Рабочий баланс спота: ${balances?.spot_working_balance?.toFixed(2) ?? '0.00'}</p>
          <p>Рабочий баланс фьючерсов: ${balances?.futures_working_balance?.toFixed(2) ?? '0.00'}</p>
        </Card>
        <Card title="Сводка PnL">
          <strong>R: {pnl?.realized_pnl?.toFixed(4) ?? '0.0000'}</strong>
          <p>U: {pnl?.unrealized_pnl?.toFixed(4) ?? '0.0000'}</p>
          <p>Открытых позиций: {pnl?.open_positions ?? 0}</p>
          <p>Win rate: {pnl?.win_rate?.toFixed(2) ?? '0.00'}%</p>
        </Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="Состояние бота">
          <p><strong>{bot?.enabled ? 'Включён' : 'Выключен'}</strong> · интервал {bot?.scan_interval_seconds ?? 0} сек</p>
          <p>Автоисполнение: {onOff(bot?.auto_execute)}</p>
          <p>Live разрешён: {yesNo(bot?.live_execution_allowed)}</p>
          <p>Последний цикл: {t(bot?.last_cycle_status)}</p>
          <p>{bot?.last_cycle_summary ?? 'Сводки по циклу пока нет.'}</p>
        </Card>
        <Card title="Последние решения стратегии">
          {decisions.length === 0 ? <p>Решений пока нет.</p> : (
            <ul>
              {decisions.map((decision) => (
                <li key={decision.id}>{decision.symbol} · {decision.allowed ? 'разрешено' : 'заблокировано'} · {t(decision.market_scenario)} · conf {decision.confidence.toFixed(2)}</li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Готовность к релизу">
          <p>Оценка: <strong>{readiness?.score ?? 0}</strong></p>
          <p>Готов к paper: {yesNo(readiness?.ready_for_paper)}</p>
          <p>Готов к live: {yesNo(readiness?.ready_for_live)}</p>
          <p>Критичных проблем: {readiness?.critical_issues.length ?? 0}</p>
          <p>Предупреждений: {readiness?.warnings.length ?? 0}</p>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Состояние операций">
          <p>Maintenance: {onOff(ops?.maintenance_mode)}</p>
          <p>Торговля на паузе: {yesNo(ops?.trading_paused)}</p>
          <p>Kill switch: {ops?.kill_switch_armed ? 'взведён' : 'выключен'}</p>
          <p>Heartbeat: {formatDateTime(ops?.last_bot_heartbeat_at)}</p>
          <p>Последний reconcile: {formatDateTime(ops?.last_reconcile_at)}</p>
          <p>Последний lifecycle sync: {formatDateTime(ops?.last_lifecycle_sync_at)}</p>
          <p>Последний flatten: {formatDateTime(ops?.last_flatten_at)} ({t(ops?.last_flatten_status)})</p>
          <p>Последнее recovery: {formatDateTime(ops?.last_recovery_at)}</p>
        </Card>
        <Card title="Кривая капитала">
          <MiniLineChart points={analytics?.recent_equity_curve ?? []} />
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Последние прогоны бэктеста">
          {runs.length === 0 ? <p>Прогонов пока нет.</p> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>ID</th><th>Инструмент</th><th>Рынок</th><th>Сделок</th><th>Win rate</th><th>PnL</th><th>PF</th><th>Цель</th></tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td>{run.id}</td>
                      <td>{run.symbol}</td>
                      <td>{t(run.market_type)}</td>
                      <td>{run.closed_trades}</td>
                      <td>{run.win_rate.toFixed(2)}%</td>
                      <td>{run.realized_pnl.toFixed(4)}</td>
                      <td>{run.profit_factor.toFixed(4)}</td>
                      <td>{run.target_metrics_met ? 'выполнена' : 'пока нет'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </Page>
  )
}
