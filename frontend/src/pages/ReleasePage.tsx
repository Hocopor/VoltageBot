import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { BackupArtifact, ReleaseAcceptanceRun, ReleaseReport } from '../types'

const defaultReport: ReleaseReport = {
  generated_at: '',
  project: 'VOLTAGE',
  version: 'unknown',
  environment: 'production',
  preflight: {
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
  },
  readiness: {
    generated_at: '',
    score: 0,
    ready_for_paper: false,
    ready_for_live: false,
    critical_issues: [],
    warnings: [],
    preflight_status: 'unknown',
    counts: { orders: 0, trades: 0, positions: 0, journal_entries: 0 },
    state: null,
  },
  codex: { connected: false, mode: 'chatgpt', message: 'Loading...', pending_login: false },
  deepseek: { configured: false, model: 'deepseek-chat', base_url: '', message: 'Loading...' },
  state: {
    maintenance_mode: false,
    trading_paused: false,
    kill_switch_armed: false,
    boot_count: 0,
    recovery_runs_count: 0,
    open_positions: 0,
    open_live_positions: 0,
    open_paper_positions: 0,
  },
  acceptance_checks: [],
  overall_status: 'unknown',
  recommended_mode: 'blocked',
  journal_entries: 0,
  bot_runs: 0,
  system_events: 0,
  backup_artifacts: [],
  release_artifacts: [],
  next_actions: [],
}

export default function ReleasePage() {
  const [report, setReport] = useState<ReleaseReport>(defaultReport)
  const [artifacts, setArtifacts] = useState<BackupArtifact[]>([])
  const [acceptanceRun, setAcceptanceRun] = useState<ReleaseAcceptanceRun | null>(null)
  const [message, setMessage] = useState('')

  const load = async () => {
    const [nextReport, nextArtifacts] = await Promise.all([
      api.getReleaseReport(),
      api.getReleaseArtifacts(),
    ])
    setReport(nextReport)
    setArtifacts(nextArtifacts)
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : String(error)))
  }, [])

  const runAcceptance = async () => {
    try {
      const result = await api.runReleaseAcceptance()
      setAcceptanceRun(result)
      setMessage(`Release acceptance completed: ${result.overall_status} · ${result.recommended_mode}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Release" subtitle="Final production acceptance, release artifacts and operator-facing go-live summary.">
      <div className="card-grid four-columns">
        <Card title="Release status">
          <p>Status: <strong>{report.overall_status}</strong></p>
          <p>Recommended mode: <strong>{report.recommended_mode}</strong></p>
          <p>Version: {report.version}</p>
          <p>Environment: {report.environment}</p>
        </Card>
        <Card title="Readiness summary">
          <p>Score: <strong>{report.readiness.score}</strong></p>
          <p>Paper ready: {report.readiness.ready_for_paper ? 'yes' : 'no'}</p>
          <p>Live ready: {report.readiness.ready_for_live ? 'yes' : 'no'}</p>
          <p>Preflight: {report.preflight.overall_status}</p>
        </Card>
        <Card title="AI integrations">
          <p>Codex: <strong>{report.codex.connected ? 'connected' : 'not connected'}</strong></p>
          <p>DeepSeek: <strong>{report.deepseek.configured ? 'configured' : 'fallback only'}</strong></p>
          <p>{report.codex.message}</p>
          <p>{report.deepseek.message}</p>
        </Card>
        <Card title="Runtime snapshot">
          <p>Journal entries: <strong>{report.journal_entries}</strong></p>
          <p>Bot runs: {report.bot_runs}</p>
          <p>System events: {report.system_events}</p>
          <p>Open positions: {report.state.open_positions}</p>
        </Card>
      </div>

      <div className="card-grid two-columns">
        <Card title="Acceptance runner">
          {message ? <p className="message-block">{message}</p> : null}
          <p>Generate final release acceptance artifacts under the configured release root.</p>
          <div className="action-row wrap">
            <button onClick={runAcceptance}>Run release acceptance</button>
          </div>
          {acceptanceRun ? (
            <div className="message-block">
              <p>Overall: <strong>{acceptanceRun.overall_status}</strong></p>
              <p>Recommended mode: {acceptanceRun.recommended_mode}</p>
              <p>JSON artifact: {acceptanceRun.json_artifact.name}</p>
              <p>Markdown artifact: {acceptanceRun.markdown_artifact.name}</p>
            </div>
          ) : <p>No acceptance run in this session yet.</p>}
        </Card>
        <Card title="Next actions">
          {report.next_actions.length ? <ul>{report.next_actions.map((item) => <li key={item}>{item}</li>)}</ul> : <p>No next actions.</p>}
        </Card>
      </div>

      <div className="card-grid two-columns">
        <Card title="Acceptance checks">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Status</th><th>Message</th></tr>
              </thead>
              <tbody>
                {report.acceptance_checks.map((item) => (
                  <tr key={item.name}><td>{item.name}</td><td>{item.status}</td><td>{item.message}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Release artifacts">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Kind</th><th>Size</th></tr>
              </thead>
              <tbody>
                {artifacts.slice(0, 12).map((item) => (
                  <tr key={item.path}><td>{item.name}</td><td>{item.kind}</td><td>{item.size_bytes}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </Page>
  )
}
