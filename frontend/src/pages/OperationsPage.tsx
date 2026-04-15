import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type {
  BackupArtifact,
  BackupManifest,
  FlattenLiveResult,
  FlattenPaperResult,
  FlattenRun,
  PreflightStatus,
  ReconcileRun,
  RecoveryRun,
  ReleaseReadiness,
  SystemState,
} from '../types'

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
      api.getOpsState(),
      api.getPreflight(),
      api.getReleaseReadiness(),
      api.getReconcileRuns(),
      api.getRecoveryRuns(),
      api.getFlattenRuns(),
      api.getBackupArtifacts(),
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
      setMessage('Operations controls saved')
      setReadiness(await api.getReleaseReadiness())
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const reconcile = async () => {
    try {
      const run = await api.reconcileLive()
      setMessage(`Live reconcile #${run.id}: ${run.summary ?? run.status}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const recover = async () => {
    try {
      const run = await api.runRecovery()
      setMessage(`Recovery #${run.id}: ${run.summary ?? run.status}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const flattenPaper = async () => {
    try {
      const result = await api.flattenPaper()
      setFlattenResult(result)
      setMessage(`Flattened ${result.closed_positions} paper positions`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const flattenLive = async (armKillSwitch: boolean) => {
    try {
      const result = armKillSwitch ? await api.flattenLiveKillSwitch() : await api.flattenLive()
      setLiveFlatten(result)
      setMessage(`Live flatten run #${result.run_id}: ${result.summary ?? result.status}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const createManifest = async () => {
    try {
      const next = await api.createBackupManifest()
      setManifest(next)
      setMessage(`Manifest created: ${next.name}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Operations" subtitle="Production controls, readiness, backups, recovery workflows and live account safety state.">
      <div className="card-grid four-columns">
        <Card title="System state">
          <p>Boot count: <strong>{state.boot_count}</strong></p>
          <p>Last startup: {state.last_startup_at ?? 'n/a'}</p>
          <p>Last shutdown: {state.last_shutdown_at ?? 'n/a'}</p>
          <p>Last reconcile: {state.last_reconcile_at ?? 'n/a'}</p>
          <p>Last lifecycle sync: {state.last_lifecycle_sync_at ?? 'n/a'}</p>
          <p>Last recovery: {state.last_recovery_at ?? 'n/a'}</p>
        </Card>
        <Card title="Open positions">
          <p>Total: <strong>{state.open_positions}</strong></p>
          <p>Live: {state.open_live_positions}</p>
          <p>Paper: {state.open_paper_positions}</p>
          {flattenResult ? <p>Last paper flatten: {flattenResult.closed_positions}</p> : null}
          {liveFlatten ? <p>Last live flatten submissions: {liveFlatten.close_orders_submitted}</p> : null}
        </Card>
        <Card title="Preflight">
          <p>Status: <strong>{preflight.overall_status}</strong></p>
          <p>Environment: {preflight.environment}</p>
          <p>DB: {preflight.database_scheme}</p>
          <p>Redis: {preflight.redis_scheme}</p>
          <p>Cloudflare: {preflight.cloudflare_configured ? 'configured' : 'not configured'}</p>
        </Card>
        <Card title="Release readiness">
          <p>Score: <strong>{readiness.score}</strong></p>
          <p>Paper ready: {readiness.ready_for_paper ? 'yes' : 'no'}</p>
          <p>Live ready: {readiness.ready_for_live ? 'yes' : 'no'}</p>
          <p>Critical: {readiness.critical_issues.length}</p>
          <p>Warnings: {readiness.warnings.length}</p>
        </Card>
      </div>

      <div className="card-grid two-columns">
        <Card title="Controls">
          {message ? <p className="message-block">{message}</p> : null}
          <label><input type="checkbox" checked={state.maintenance_mode} onChange={(e) => setState({ ...state, maintenance_mode: e.target.checked })} /> Maintenance</label>
          <label><input type="checkbox" checked={state.trading_paused} onChange={(e) => setState({ ...state, trading_paused: e.target.checked })} /> Pause trading</label>
          <label><input type="checkbox" checked={state.kill_switch_armed} onChange={(e) => setState({ ...state, kill_switch_armed: e.target.checked })} /> Kill switch</label>
          <div className="actions-row">
            <button onClick={saveControls}>Save</button>
            <button onClick={reconcile}>Reconcile live</button>
            <button onClick={recover}>Run recovery</button>
            <button onClick={flattenPaper}>Flatten paper</button>
          </div>
          <div className="actions-row" style={{ marginTop: 8 }}>
            <button onClick={() => flattenLive(false)}>Flatten live</button>
            <button onClick={() => flattenLive(true)}>Flatten live + arm kill switch</button>
            <button onClick={createManifest}>Create manifest</button>
          </div>
          {manifest ? <p>Latest manifest: {manifest.name}</p> : null}
        </Card>
        <Card title="Readiness blockers">
          <p><strong>Critical issues</strong></p>
          {readiness.critical_issues.length === 0 ? <p>None.</p> : <ul>{readiness.critical_issues.map((item) => <li key={item}>{item}</li>)}</ul>}
          <p><strong>Warnings</strong></p>
          {readiness.warnings.length === 0 ? <p>None.</p> : <ul>{readiness.warnings.map((item) => <li key={item}>{item}</li>)}</ul>}
        </Card>
      </div>

      <div className="card-grid three-columns">
        <Card title="Preflight checks">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Status</th><th>Message</th></tr>
              </thead>
              <tbody>
                {preflight.checks.map((item) => (
                  <tr key={item.name}><td>{item.name}</td><td>{item.status}</td><td>{item.message}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Readiness counts">
          <p>Orders: <strong>{readiness.counts.orders}</strong></p>
          <p>Trades: {readiness.counts.trades}</p>
          <p>Positions: {readiness.counts.positions}</p>
          <p>Journal entries: {readiness.counts.journal_entries}</p>
          <p>Backup root: {preflight.backup_root || 'n/a'}</p>
          <p>Release root: {preflight.release_root || 'n/a'}</p>
        </Card>
        <Card title="Backup artifacts">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Kind</th><th>Size</th></tr>
              </thead>
              <tbody>
                {backups.slice(0, 8).map((item) => (
                  <tr key={item.path}><td>{item.name}</td><td>{item.kind}</td><td>{item.size_bytes}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="card-grid three-columns">
        <Card title="Reconcile history">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Status</th><th>Balances</th><th>Orders</th><th>Positions</th><th>Closed local</th></tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>{run.id}</td><td>{run.status}</td><td>{run.balances_synced}</td><td>{run.orders_seen}</td><td>{run.positions_seen}</td><td>{run.closed_local_positions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Recovery history">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Context</th><th>Status</th><th>Stale bot runs</th><th>Recovered positions</th></tr>
              </thead>
              <tbody>
                {recoveryRuns.map((run) => (
                  <tr key={run.id}>
                    <td>{run.id}</td><td>{run.startup_context}</td><td>{run.status}</td><td>{run.stale_bot_runs}</td><td>{run.recovered_positions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Flatten history">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Status</th><th>Cancelled</th><th>Close orders</th><th>Symbols</th></tr>
              </thead>
              <tbody>
                {flattenRuns.map((run) => (
                  <tr key={run.id}>
                    <td>{run.id}</td><td>{run.status}</td><td>{run.orders_cancelled}</td><td>{run.close_orders_submitted}</td><td>{run.symbols_touched}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Page>
  )
}
