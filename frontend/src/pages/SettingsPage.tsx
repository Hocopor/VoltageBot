import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { CodexStatus, RuntimeSettings } from '../types'

const defaultState: RuntimeSettings = {
  mode: 'paper',
  spot_enabled: true,
  futures_enabled: false,
  paper_start_balance: 10000,
  history_start_balance: 10000,
  spot_working_balance: 1000,
  futures_working_balance: 1000,
  notes: '',
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<RuntimeSettings>(defaultState)
  const [message, setMessage] = useState('')
  const [codexStatus, setCodexStatus] = useState<CodexStatus | null>(null)

  useEffect(() => {
    api.getSettings().then(setSettings)
    api.getCodexStatus().then(setCodexStatus)
  }, [])

  const save = async () => {
    const result = await api.updateSettings(settings)
    setSettings(result)
    setMessage('Runtime settings saved')
  }

  const connectCodex = async () => {
    const result = await api.mockConnectCodex()
    setCodexStatus(result)
    setMessage('Codex placeholder session saved')
  }

  return (
    <Page title="Runtime settings" subtitle="Mode, balances and market toggles.">
      <div className="card-grid two-columns">
        <Card title="Execution mode">
          <label className="field">
            <span>Mode</span>
            <select value={settings.mode} onChange={(e) => setSettings({ ...settings, mode: e.target.value as RuntimeSettings['mode'] })}>
              <option value="live">live</option>
              <option value="paper">paper</option>
              <option value="historical">historical</option>
            </select>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={settings.spot_enabled} onChange={(e) => setSettings({ ...settings, spot_enabled: e.target.checked })} />
            <span>Enable spot</span>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={settings.futures_enabled} onChange={(e) => setSettings({ ...settings, futures_enabled: e.target.checked })} />
            <span>Enable futures</span>
          </label>
        </Card>
        <Card title="Balances">
          <label className="field">
            <span>Paper start balance</span>
            <input type="number" value={settings.paper_start_balance} onChange={(e) => setSettings({ ...settings, paper_start_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Historical start balance</span>
            <input type="number" value={settings.history_start_balance} onChange={(e) => setSettings({ ...settings, history_start_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Spot working balance</span>
            <input type="number" value={settings.spot_working_balance} onChange={(e) => setSettings({ ...settings, spot_working_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Futures working balance</span>
            <input type="number" value={settings.futures_working_balance} onChange={(e) => setSettings({ ...settings, futures_working_balance: Number(e.target.value) })} />
          </label>
        </Card>
        <Card title="Codex login placeholder">
          <p>Status: {codexStatus?.connected ? 'connected' : 'not connected'}</p>
          <p>{codexStatus?.message ?? 'No session yet'}</p>
          <button onClick={connectCodex}>Save placeholder login</button>
          <p>Full browser-login flow is available on the Integrations page.</p>
        </Card>
      </div>
      <div className="action-row">
        <button onClick={save}>Save settings</button>
        {message ? <span className="message">{message}</span> : null}
      </div>
    </Page>
  )
}
