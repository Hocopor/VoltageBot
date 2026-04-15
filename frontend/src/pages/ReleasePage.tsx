import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, t, yesNo } from '../format'
import type { BackupArtifact, ReleaseAcceptanceRun, ReleaseReport } from '../types'

const emptyReport: ReleaseReport = {
  generated_at: '', project: '', version: '', environment: '', preflight: { generated_at: '', environment: '', database_scheme: '', redis_scheme: '', backup_root: '', release_root: '', codex_session_dir: '', cloudflare_configured: false, checks: [], overall_status: 'unknown' }, readiness: { generated_at: '', score: 0, ready_for_paper: false, ready_for_live: false, critical_issues: [], warnings: [], preflight_status: 'unknown', counts: { orders: 0, trades: 0, positions: 0, journal_entries: 0 }, state: null }, codex: { connected: false, mode: 'chatgpt', message: 'Загрузка...', pending_login: false }, deepseek: { configured: false, model: '', base_url: '', message: 'Загрузка...' }, state: { maintenance_mode: false, trading_paused: false, kill_switch_armed: false, boot_count: 0, recovery_runs_count: 0, open_positions: 0, open_live_positions: 0, open_paper_positions: 0 }, acceptance_checks: [], overall_status: 'unknown', recommended_mode: 'paper', journal_entries: 0, bot_runs: 0, system_events: 0, backup_artifacts: [], release_artifacts: [], next_actions: [] }

export default function ReleasePage() {
  const [report, setReport] = useState<ReleaseReport>(emptyReport)
  const [artifacts, setArtifacts] = useState<BackupArtifact[]>([])
  const [acceptanceRun, setAcceptanceRun] = useState<ReleaseAcceptanceRun | null>(null)
  const [message, setMessage] = useState('')

  const load = async () => {
    const [releaseReport, releaseArtifacts] = await Promise.all([api.getReleaseReport(), api.getReleaseArtifacts()])
    setReport(releaseReport)
    setArtifacts(releaseArtifacts)
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : String(error)))
  }, [])

  const runAcceptance = async () => {
    try {
      const result = await api.runReleaseAcceptance()
      setAcceptanceRun(result)
      setMessage(`Acceptance run: ${t(result.overall_status)}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Релиз" subtitle="Сводный отчёт по релизу, готовность, acceptance run и релизные артефакты.">
      <div className="card-grid four-columns">
        <Card title="Общий статус"><p><strong>{t(report.overall_status)}</strong></p><p>Сформировано: {formatDateTime(report.generated_at)}</p><p>Версия: {report.version || '—'}</p><p>Окружение: {report.environment || '—'}</p></Card>
        <Card title="Readiness"><p>Оценка: <strong>{report.readiness.score}</strong></p><p>Paper: {yesNo(report.readiness.ready_for_paper)}</p><p>Live: {yesNo(report.readiness.ready_for_live)}</p><p>Рекомендованный режим: {t(report.recommended_mode)}</p></Card>
        <Card title="Интеграции"><p>Codex: {yesNo(report.codex.connected)}</p><p>DeepSeek: {yesNo(report.deepseek.configured)}</p><p>Cloudflare: {yesNo(report.preflight.cloudflare_configured)}</p><p>Preflight: {t(report.preflight.overall_status)}</p></Card>
        <Card title="Счётчики"><p>Записи дневника: <strong>{report.journal_entries}</strong></p><p>Bot runs: {report.bot_runs}</p><p>Системные события: {report.system_events}</p><p>Открытые позиции: {report.state.open_positions}</p></Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Acceptance runner">
          {message ? <p className="message-block">{message}</p> : null}
          <p>Сформировать финальные acceptance-артефакты в папке releases.</p>
          <div className="action-row wrap"><button onClick={runAcceptance}>Запустить release acceptance</button></div>
          {acceptanceRun ? <div className="message-block"><p>Статус: <strong>{t(acceptanceRun.overall_status)}</strong></p><p>Рекомендуемый режим: {t(acceptanceRun.recommended_mode)}</p><p>JSON: {acceptanceRun.json_artifact.name}</p><p>Markdown: {acceptanceRun.markdown_artifact.name}</p></div> : <p>Acceptance run ещё не запускался.</p>}
        </Card>
        <Card title="Следующие действия">{report.next_actions.length ? <ul>{report.next_actions.map((item) => <li key={item}>{item}</li>)}</ul> : <p>Следующих действий нет.</p>}</Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Acceptance checks"><div className="table-wrap"><table><thead><tr><th>Название</th><th>Статус</th><th>Сообщение</th></tr></thead><tbody>{report.acceptance_checks.map((item) => <tr key={item.name}><td>{item.name}</td><td>{t(item.status)}</td><td>{item.message}</td></tr>)}</tbody></table></div></Card>
        <Card title="Релизные артефакты"><div className="table-wrap"><table><thead><tr><th>Имя</th><th>Тип</th><th>Размер</th></tr></thead><tbody>{artifacts.slice(0, 12).map((item) => <tr key={item.path}><td>{item.name}</td><td>{item.kind}</td><td>{item.size_bytes}</td></tr>)}</tbody></table></div></Card>
      </div>
    </Page>
  )
}
