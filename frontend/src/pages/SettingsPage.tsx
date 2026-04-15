import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { t, yesNo } from '../format'
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
    setMessage('Настройки сохранены.')
  }

  const connectCodex = async () => {
    const result = await api.mockConnectCodex()
    setCodexStatus(result)
    setMessage('Тестовая сессия Codex сохранена.')
  }

  return (
    <Page title="Настройки режима" subtitle="Режим работы, балансы и переключатели рынков.">
      <div className="card-grid two-columns">
        <Card title="Режим исполнения">
          <label className="field">
            <span>Режим</span>
            <select value={settings.mode} onChange={(e) => setSettings({ ...settings, mode: e.target.value as RuntimeSettings['mode'] })}>
              <option value="live">Реальный</option>
              <option value="paper">Бумажный</option>
              <option value="historical">Исторический</option>
            </select>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={settings.spot_enabled} onChange={(e) => setSettings({ ...settings, spot_enabled: e.target.checked })} />
            <span>Включить спот</span>
          </label>
          <label className="checkbox-row">
            <input type="checkbox" checked={settings.futures_enabled} onChange={(e) => setSettings({ ...settings, futures_enabled: e.target.checked })} />
            <span>Включить фьючерсы</span>
          </label>
        </Card>
        <Card title="Балансы">
          <label className="field">
            <span>Стартовый баланс paper</span>
            <input type="number" value={settings.paper_start_balance} onChange={(e) => setSettings({ ...settings, paper_start_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Стартовый баланс historical</span>
            <input type="number" value={settings.history_start_balance} onChange={(e) => setSettings({ ...settings, history_start_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Рабочий баланс спота</span>
            <input type="number" value={settings.spot_working_balance} onChange={(e) => setSettings({ ...settings, spot_working_balance: Number(e.target.value) })} />
          </label>
          <label className="field">
            <span>Рабочий баланс фьючерсов</span>
            <input type="number" value={settings.futures_working_balance} onChange={(e) => setSettings({ ...settings, futures_working_balance: Number(e.target.value) })} />
          </label>
        </Card>
        <Card title="Заглушка входа Codex">
          <p>Статус: {codexStatus?.connected ? 'подключено' : 'не подключено'}</p>
          <p>{codexStatus?.message ?? 'Сессии пока нет.'}</p>
          <p>Режим: {t(codexStatus?.mode)}</p>
          <p>Подключено: {yesNo(codexStatus?.connected)}</p>
          <button onClick={connectCodex}>Сохранить тестовую сессию</button>
          <p>Полный вход через браузер доступен на странице «Интеграции».</p>
        </Card>
      </div>
      <div className="action-row">
        <button onClick={save}>Сохранить настройки</button>
        {message ? <span className="message">{message}</span> : null}
      </div>
    </Page>
  )
}
