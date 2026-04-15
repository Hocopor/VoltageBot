import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, MiniLineChart, Page } from '../components'
import type { AnalyticsOverview, BacktestRun, BalanceOverview, BotConfig, PnlOverview, ReleaseReadiness, RuntimeSettings, StrategyDecision, SystemState } from '../types'

export default function DashboardPage() {
  const [health, setHealth] = useState<string>('loading')
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
    api.health().then((data) => setHealth(`${data.status} · ${data.service}`)).catch(() => setHealth('unavailable'))
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
    <Page title="Dashboard" subtitle="Operational overview for runtime mode, balances, strategy decisions, bot runtime and production safety state.">
      <div className="card-grid four-columns">
        <Card title="API health">
          <strong>{health}</strong>
        </Card>
        <Card title="Runtime mode">
          <strong>{settings?.mode ?? 'n/a'}</strong>
          <p>Spot: {settings?.spot_enabled ? 'on' : 'off'}</p>
          <p>Futures: {settings?.futures_enabled ? 'on' : 'off'}</p>
        </Card>
        <Card title="Wallet overview">
          <strong>${balances?.total_wallet_usd?.toFixed(2) ?? '0.00'}</strong>
          <p>Spot working balance: ${balances?.spot_working_balance?.toFixed(2) ?? '0.00'}</p>
          <p>Futures working balance: ${balances?.futures_working_balance?.toFixed(2) ?? '0.00'}</p>
        </Card>
        <Card title="PnL overview">
          <strong>R: {pnl?.realized_pnl?.toFixed(4) ?? '0.0000'}</strong>
          <p>U: {pnl?.unrealized_pnl?.toFixed(4) ?? '0.0000'}</p>
          <p>Open positions: {pnl?.open_positions ?? 0}</p>
          <p>Win rate: {pnl?.win_rate?.toFixed(2) ?? '0.00'}%</p>
        </Card>
      </div>
      <div className="card-grid three-columns">
        <Card title="Bot runtime status">
          <p><strong>{bot?.enabled ? 'enabled' : 'disabled'}</strong> · interval {bot?.scan_interval_seconds ?? 0}s</p>
          <p>Auto execute: {bot?.auto_execute ? 'on' : 'off'}</p>
          <p>Live execution allowed: {bot?.live_execution_allowed ? 'yes' : 'no'}</p>
          <p>Last cycle: {bot?.last_cycle_status ?? 'n/a'}</p>
          <p>{bot?.last_cycle_summary ?? 'No cycle summary yet.'}</p>
        </Card>
        <Card title="Latest strategy decisions">
          {decisions.length === 0 ? <p>No decisions yet.</p> : (
            <ul>
              {decisions.map((decision) => (
                <li key={decision.id}>{decision.symbol} · {decision.allowed ? 'allowed' : 'blocked'} · {decision.market_scenario} · conf {decision.confidence.toFixed(2)}</li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Release readiness">
          <p>Score: <strong>{readiness?.score ?? 0}</strong></p>
          <p>Paper ready: {readiness?.ready_for_paper ? 'yes' : 'no'}</p>
          <p>Live ready: {readiness?.ready_for_live ? 'yes' : 'no'}</p>
          <p>Critical issues: {readiness?.critical_issues.length ?? 0}</p>
          <p>Warnings: {readiness?.warnings.length ?? 0}</p>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Operations state">
          <p>Maintenance: {ops?.maintenance_mode ? 'on' : 'off'}</p>
          <p>Trading paused: {ops?.trading_paused ? 'yes' : 'no'}</p>
          <p>Kill switch: {ops?.kill_switch_armed ? 'armed' : 'off'}</p>
          <p>Heartbeat: {ops?.last_bot_heartbeat_at ?? 'n/a'}</p>
          <p>Last reconcile: {ops?.last_reconcile_at ?? 'n/a'}</p>
          <p>Last lifecycle sync: {ops?.last_lifecycle_sync_at ?? 'n/a'}</p>
          <p>Last flatten: {ops?.last_flatten_at ?? 'n/a'} ({ops?.last_flatten_status ?? 'n/a'})</p>
          <p>Last recovery: {ops?.last_recovery_at ?? 'n/a'}</p>
        </Card>
        <Card title="Recent equity curve">
          <MiniLineChart points={analytics?.recent_equity_curve ?? []} />
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Latest backtest runs">
          {runs.length === 0 ? <p>No runs yet.</p> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>ID</th><th>Symbol</th><th>Market</th><th>Trades</th><th>Win rate</th><th>PnL</th><th>PF</th><th>Target</th></tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td>{run.id}</td>
                      <td>{run.symbol}</td>
                      <td>{run.market_type}</td>
                      <td>{run.closed_trades}</td>
                      <td>{run.win_rate.toFixed(2)}%</td>
                      <td>{run.realized_pnl.toFixed(4)}</td>
                      <td>{run.profit_factor.toFixed(4)}</td>
                      <td>{run.target_metrics_met ? 'met' : 'not yet'}</td>
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
