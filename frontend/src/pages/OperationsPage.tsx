import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, t, yesNo } from '../format'
import type { BackupArtifact, BackupManifest, FlattenLiveResult, FlattenPaperResult, FlattenRun, PreflightStatus, ReconcileRun, RecoveryRun, ReleaseReadiness, SystemState } from '../types'

const defaultState: SystemState = {
  maintenance_mode: false,
  trading_paused: false,
  kill_switch_armed: false,
  boot_count: 0,
  last_startup_at: null,
  last_shutdown_at: null,
  last_bot_heartbeat_at: null,
  last_reconcile_at: null,
  last_lifecycle_sync_at: null,
  last_live_sync_status: null,
  last_live_sync_message: null,
  recovery_runs_count: 0,
  last_recovery_at: null,
  last_flatten_at: null,
  last_flatten_status: null,
  last_flatten_message: null,
  open_positions: 0,
  open_live_positions: 0,
  open_paper_positions: 0,
}

const defaultPreflight: PreflightStatus = {
  generated_at: '',
  environment: 'production',
  database_scheme: 'unknown',
  redis_scheme: 'unknown',
  backup_root: '',
  release_root: '',
  codex_session_dir: '',
  cloudflare_configured: false,
  checks: [],
  overall_status: 'unknown',
}

const defaultReadiness: ReleaseReadiness = {
  generated_at: '',
  score: 0,
  ready_for_paper: false,
  ready_for_live: false,
  critical_issues: [],
  warnings: [],
  preflight_status: 'unknown',
  counts: { orders: 0, trades: 0, positions: 0, journal_entries: 0 },
  state: null,
}

export default function OperationsPage() {
  const [state, setState] = useState<SystemState>(defaultState)
  const [preflight, setPreflight] = useState<PreflightStatus>(defaultPreflight)
  const [readiness, setReadiness] = useState<ReleaseReadiness>(defaultReadiness)
  const [runs, setRuns] = useState<ReconcileRun[]>([])
  const [recoveryRuns, setRecoveryRuns] = useState<RecoveryRun[]>([])
  const [flattenRuns, setFlattenRuns] = useState<FlattenRun[]>([])
  const [backups, setBackups] = useState<BackupArtifact[]>([])
  const [message, setMessage] = useState('')
  const [flattenResult, setFlattenResult] = useState<FlattenPaperResult | null>(null)
  const [liveFlatten, setLiveFlatten] = useState<FlattenLiveResult | null>(null)
  const [manifest, setManifest] = useState<BackupManifest | null>(null)

  const load = async () => {
    const [s, pf, ready, history, recoveryHistory, flattenHistory, backupArtifacts] = await Promise.all([
      api.getOpsState(), api.getPreflight(), api.getReleaseReadiness(), api.getReconcileRuns(), api.getRecoveryRuns(), api.getFlattenRuns(), api.getBackupArtifacts(),
    ])
    setState(s)
    setPreflight(pf)
    setReadiness(ready)
    setRuns(history)
    setRecoveryRuns(recoveryHistory)
    setFlattenRuns(flattenHistory)
    setBackups(backupArtifacts)
  }

  useEffect(() => {
    load().catch((error) => setMessage(String(error)))
  }, [])

  const saveControls = async () => {
    try {
      setState(await api.updateOpsState(state))
      setMessage('Операционные флаги сохранены.')
      setReadiness(await api.getReleaseReadiness())
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) }
  }
  const reconcile = async () => { try { const run = await api.reconcileLive(); setMessage(`Reconcile #${run.id}: ${run.summary ?? run.status}`); await load() } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) } }
  const recover = async () => { try { const run = await api.runRecovery(); setMessage(`Recovery #${run.id}: ${run.summary ?? run.status}`); await load() } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) } }
  const flattenPaper = async () => { try { const result = await api.flattenPaper(); setFlattenResult(result); setMessage(`Paper-позиций закрыто: ${result.closed_positions}`); await load() } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) } }
  const flattenLive = async (armKillSwitch: boolean) => { try { const result = armKillSwitch ? await api.flattenLiveKillSwitch() : await api.flattenLive(); setLiveFlatten(result); setMessage(`Live flatten #${result.run_id}: ${result.summary ?? result.status}`); await load() } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) } }
  const createManifest = async () => { try { const next = await api.createBackupManifest(); setManifest(next); setMessage(`Manifest создан: ${next.name}`); await load() } catch (error) { setMessage(error instanceof Error ? error.message : String(error)) } }

  return (
    <Page title="Операции" subtitle="Production-контроль, readiness, резервные копии, recovery и безопасность live-аккаунта.">
      <div className="card-grid four-columns">
        <Card title="Состояние системы">
          <p>Перезапусков: <strong>{state.boot_count}</strong></p>
          <p>Последний старт: {formatDateTime(state.last_startup_at)}</p>
          <p>Последний shutdown: {formatDateTime(state.last_shutdown_at)}</p>
          <p>Последний reconcile: {formatDateTime(state.last_reconcile_at)}</p>
          <p>Последний lifecycle sync: {formatDateTime(state.last_lifecycle_sync_at)}</p>
          <p>Последнее recovery: {formatDateTime(state.last_recovery_at)}</p>
        </Card>
        <Card title="Открытые позиции">
          <p>Всего: <strong>{state.open_positions}</strong></p>
          <p>Live: {state.open_live_positions}</p>
          <p>Paper: {state.open_paper_positions}</p>
          {flattenResult ? <p>Последний paper flatten: {flattenResult.closed_positions}</p> : null}
          {liveFlatten ? <p>Последний live flatten: {liveFlatten.close_orders_submitted}</p> : null}
        </Card>
        <Card title="Preflight">
          <p>Статус: <strong>{t(preflight.overall_status)}</strong></p>
          <p>Окружение: {preflight.environment}</p>
          <p>БД: {preflight.database_scheme}</p>
          <p>Redis: {preflight.redis_scheme}</p>
          <p>Cloudflare: {preflight.cloudflare_configured ? 'настроен' : 'не настроен'}</p>
        </Card>
        <Card title="Готовность к релизу">
          <p>Оценка: <strong>{readiness.score}</strong></p>
          <p>Готов к paper: {yesNo(readiness.ready_for_paper)}</p>
          <p>Готов к live: {yesNo(readiness.ready_for_live)}</p>
          <p>Критичных: {readiness.critical_issues.length}</p>
          <p>Предупреждений: {readiness.warnings.length}</p>
        </Card>
      </div>

      <div className="card-grid two-columns">
        <Card title="Управление">
          {message ? <p className="message-block">{message}</p> : null}
          <label className="checkbox-row"><input type="checkbox" checked={state.maintenance_mode} onChange={(e) => setState({ ...state, maintenance_mode: e.target.checked })} /><span>Maintenance mode</span></label>
          <label className="checkbox-row"><input type="checkbox" checked={state.trading_paused} onChange={(e) => setState({ ...state, trading_paused: e.target.checked })} /><span>Пауза торговли</span></label>
          <label className="checkbox-row"><input type="checkbox" checked={state.kill_switch_armed} onChange={(e) => setState({ ...state, kill_switch_armed: e.target.checked })} /><span>Kill switch</span></label>
          <div className="action-row">
            <button onClick={saveControls}>Сохранить</button>
            <button onClick={reconcile}>Reconcile live</button>
            <button onClick={recover}>Запустить recovery</button>
            <button onClick={flattenPaper}>Flatten paper</button>
          </div>
          <div className="action-row">
            <button onClick={() => flattenLive(false)}>Flatten live</button>
            <button onClick={() => flattenLive(true)}>Flatten live + kill switch</button>
            <button onClick={createManifest}>Создать manifest</button>
          </div>
          {manifest ? <p>Последний manifest: {manifest.name}</p> : null}
        </Card>
        <Card title="Блокирующие факторы">
          <p><strong>Критичные проблемы</strong></p>
          {readiness.critical_issues.length === 0 ? <p>Нет.</p> : <ul>{readiness.critical_issues.map((item) => <li key={item}>{item}</li>)}</ul>}
          <p><strong>Предупреждения</strong></p>
          {readiness.warnings.length === 0 ? <p>Нет.</p> : <ul>{readiness.warnings.map((item) => <li key={item}>{item}</li>)}</ul>}
        </Card>
      </div>

      <div className="card-grid three-columns">
        <Card title="Проверки preflight">
          <div className="table-wrap"><table><thead><tr><th>Название</th><th>Статус</th><th>Сообщение</th></tr></thead><tbody>{preflight.checks.map((item) => <tr key={item.name}><td>{item.name}</td><td>{t(item.status)}</td><td>{item.message}</td></tr>)}</tbody></table></div>
        </Card>
        <Card title="Счётчики readiness">
          <p>Ордера: <strong>{readiness.counts.orders}</strong></p>
          <p>Сделки: {readiness.counts.trades}</p>
          <p>Позиции: {readiness.counts.positions}</p>
          <p>Записи дневника: {readiness.counts.journal_entries}</p>
          <p>Папка backups: {preflight.backup_root || '—'}</p>
          <p>Папка releases: {preflight.release_root || '—'}</p>
        </Card>
        <Card title="Резервные копии">
          <div className="table-wrap"><table><thead><tr><th>Имя</th><th>Тип</th><th>Размер</th></tr></thead><tbody>{backups.slice(0, 8).map((item) => <tr key={item.path}><td>{item.name}</td><td>{item.kind}</td><td>{item.size_bytes}</td></tr>)}</tbody></table></div>
        </Card>
      </div>

      <div className="card-grid three-columns">
        <Card title="История reconcile"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Статус</th><th>Балансы</th><th>Ордера</th><th>Позиции</th><th>Создано</th></tr></thead><tbody>{runs.map((item) => <tr key={item.id}><td>{item.id}</td><td>{t(item.status)}</td><td>{item.balances_synced}</td><td>{item.orders_seen}</td><td>{item.positions_seen}</td><td>{formatDateTime(item.created_at)}</td></tr>)}</tbody></table></div></Card>
        <Card title="История recovery"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Статус</th><th>Stale runs</th><th>Позиций</th><th>Создано</th></tr></thead><tbody>{recoveryRuns.map((item) => <tr key={item.id}><td>{item.id}</td><td>{t(item.status)}</td><td>{item.stale_bot_runs}</td><td>{item.recovered_positions}</td><td>{formatDateTime(item.created_at)}</td></tr>)}</tbody></table></div></Card>
        <Card title="История flatten"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Режим</th><th>Scope</th><th>Статус</th><th>Close orders</th><th>Создано</th></tr></thead><tbody>{flattenRuns.map((item) => <tr key={item.id}><td>{item.id}</td><td>{t(item.mode)}</td><td>{item.scope}</td><td>{t(item.status)}</td><td>{item.close_orders_submitted}</td><td>{formatDateTime(item.created_at)}</td></tr>)}</tbody></table></div></Card>
      </div>
    </Page>
  )
}
