import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { BotConfig, BotCycleResult, BotRun, SystemEvent } from '../types'

const defaultConfig: BotConfig = {
  enabled: false,
  auto_execute: true,
  live_execution_allowed: false,
  scan_interval_seconds: 300,
  strategy_timeframe: '1H',
  strategy_candles: 240,
  risk_percent: 0.01,
  max_new_positions_per_cycle: 2,
  notes: '',
  last_cycle_started_at: null,
  last_cycle_finished_at: null,
  last_cycle_status: null,
  last_cycle_summary: null,
  last_error: null,
}

export default function BotPage() {
  const [config, setConfig] = useState<BotConfig>(defaultConfig)
  const [runs, setRuns] = useState<BotRun[]>([])
  const [events, setEvents] = useState<SystemEvent[]>([])
  const [message, setMessage] = useState('')
  const [lastResult, setLastResult] = useState<BotCycleResult | null>(null)

  const load = async () => {
    const [cfg, runList, eventList] = await Promise.all([api.getBotConfig(), api.getBotRuns(), api.getBotEvents()])
    setConfig(cfg)
    setRuns(runList)
    setEvents(eventList)
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : String(error)))
  }, [])

  const save = async () => {
    try {
      const saved = await api.updateBotConfig(config)
      setConfig(saved)
      setMessage('Bot config saved')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const runCycle = async () => {
    try {
      const result = await api.runBotCycle()
      setLastResult(result)
      setMessage(`Cycle #${result.run_id} ${result.status}: executed ${result.executed_total}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Bot runtime" subtitle="Automatic strategy scanning, execution controls, cycle history and system events.">
      <div className="card-grid two-columns">
        <Card title="Bot controls">
          <label className="checkbox-row">
            <input type="checkbox" checked={config.enabled} onChange={(e) => setConfig({ ...config, enabled: e.target.checked })} />
            <span>Enable automatic cycles</span>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={config.auto_execute} onChange={(e) => setConfig({ ...config, auto_execute: e.target.checked })} />
            <span>Auto-execute allowed signals</span>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={config.live_execution_allowed} onChange={(e) => setConfig({ ...config, live_execution_allowed: e.target.checked })} />
            <span>Allow live execution when runtime mode = live</span>
          </label>
          <label className="field"><span>Scan interval, seconds</span><input type="number" value={config.scan_interval_seconds} onChange={(e) => setConfig({ ...config, scan_interval_seconds: Number(e.target.value) })} /></label>
          <label className="field"><span>Strategy timeframe</span><select value={config.strategy_timeframe} onChange={(e) => setConfig({ ...config, strategy_timeframe: e.target.value as BotConfig['strategy_timeframe'] })}><option value="15M">15M</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option></select></label>
          <label className="field"><span>Strategy candles</span><input type="number" value={config.strategy_candles} onChange={(e) => setConfig({ ...config, strategy_candles: Number(e.target.value) })} /></label>
          <label className="field"><span>Risk percent</span><input type="number" step="0.001" value={config.risk_percent} onChange={(e) => setConfig({ ...config, risk_percent: Number(e.target.value) })} /></label>
          <label className="field"><span>Max new positions per cycle</span><input type="number" value={config.max_new_positions_per_cycle} onChange={(e) => setConfig({ ...config, max_new_positions_per_cycle: Number(e.target.value) })} /></label>
          <label className="field"><span>Notes</span><textarea rows={4} value={config.notes ?? ''} onChange={(e) => setConfig({ ...config, notes: e.target.value })} /></label>
          <div className="action-row wrap">
            <button onClick={save}>Save bot config</button>
            <button onClick={runCycle}>Run cycle now</button>
          </div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Current status">
          <p><strong>Status:</strong> {config.enabled ? 'enabled' : 'disabled'}</p>
          <p><strong>Last cycle status:</strong> {config.last_cycle_status ?? 'n/a'}</p>
          <p><strong>Last started:</strong> {config.last_cycle_started_at ?? 'n/a'}</p>
          <p><strong>Last finished:</strong> {config.last_cycle_finished_at ?? 'n/a'}</p>
          <p><strong>Summary:</strong> {config.last_cycle_summary ?? 'n/a'}</p>
          <p><strong>Last error:</strong> {config.last_error ?? 'none'}</p>
          {lastResult ? <p className="message-block">Manual run #{lastResult.run_id}: {lastResult.summary}</p> : null}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Cycle history">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Mode</th><th>Trigger</th><th>Status</th><th>Scanned</th><th>Allowed</th><th>Executed</th><th>Summary</th></tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>{run.id}</td>
                    <td>{run.mode}</td>
                    <td>{run.trigger_type}</td>
                    <td>{run.status}</td>
                    <td>{run.scanned_pairs}</td>
                    <td>{run.allowed_total}</td>
                    <td>{run.executed_total}</td>
                    <td>{run.summary ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="System events">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Time</th><th>Level</th><th>Source</th><th>Type</th><th>Message</th></tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{new Date(event.created_at).toLocaleString()}</td>
                    <td>{event.level}</td>
                    <td>{event.source}</td>
                    <td>{event.event_type}</td>
                    <td>{event.message}</td>
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
