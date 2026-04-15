import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, onOff, t, yesNo } from '../format'
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
      setMessage('Конфигурация бота сохранена.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const runCycle = async () => {
    try {
      const result = await api.runBotCycle()
      setLastResult(result)
      setMessage(`Цикл бота #${result.run_id} выполнен: ${result.summary}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Бот" subtitle="Конфигурация автоторговли, ручной запуск циклов, журнал запусков и системные события.">
      <div className="card-grid two-columns">
        <Card title="Конфигурация бота">
          <label className="checkbox-row"><input type="checkbox" checked={config.enabled} onChange={(e) => setConfig({ ...config, enabled: e.target.checked })} /><span>Включить бота</span></label>
          <label className="checkbox-row"><input type="checkbox" checked={config.auto_execute} onChange={(e) => setConfig({ ...config, auto_execute: e.target.checked })} /><span>Автоисполнение</span></label>
          <label className="checkbox-row"><input type="checkbox" checked={config.live_execution_allowed} onChange={(e) => setConfig({ ...config, live_execution_allowed: e.target.checked })} /><span>Разрешить live-исполнение</span></label>
          <label className="field"><span>Интервал сканирования, сек</span><input type="number" value={config.scan_interval_seconds} onChange={(e) => setConfig({ ...config, scan_interval_seconds: Number(e.target.value) })} /></label>
          <label className="field"><span>Таймфрейм стратегии</span><select value={config.strategy_timeframe} onChange={(e) => setConfig({ ...config, strategy_timeframe: e.target.value as BotConfig['strategy_timeframe'] })}><option value="15M">15M</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option></select></label>
          <label className="field"><span>Свечей</span><input type="number" value={config.strategy_candles} onChange={(e) => setConfig({ ...config, strategy_candles: Number(e.target.value) })} /></label>
          <label className="field"><span>Риск на сделку</span><input type="number" step="0.01" value={config.risk_percent} onChange={(e) => setConfig({ ...config, risk_percent: Number(e.target.value) })} /></label>
          <label className="field"><span>Макс. новых позиций за цикл</span><input type="number" value={config.max_new_positions_per_cycle} onChange={(e) => setConfig({ ...config, max_new_positions_per_cycle: Number(e.target.value) })} /></label>
          <label className="field"><span>Заметки</span><textarea rows={3} value={config.notes ?? ''} onChange={(e) => setConfig({ ...config, notes: e.target.value })} /></label>
          <div className="action-row">
            <button onClick={save}>Сохранить</button>
            <button onClick={runCycle}>Запустить цикл сейчас</button>
          </div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Последний цикл">
          <p>Включён: {onOff(config.enabled)}</p>
          <p>Автоисполнение: {onOff(config.auto_execute)}</p>
          <p>Live разрешён: {yesNo(config.live_execution_allowed)}</p>
          <p>Последний статус: {t(config.last_cycle_status)}</p>
          <p>Старт: {formatDateTime(config.last_cycle_started_at)}</p>
          <p>Финиш: {formatDateTime(config.last_cycle_finished_at)}</p>
          <p>{config.last_cycle_summary ?? 'Сводка по циклу пока отсутствует.'}</p>
          {config.last_error ? <p className="message-block">{config.last_error}</p> : null}
          {lastResult ? <p className="message-block">Последний ручной запуск: {lastResult.summary}</p> : null}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Запуски бота">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Режим</th><th>Статус</th><th>Триггер</th><th>Сканировано</th><th>Разрешено</th><th>Исполнено</th><th>Ошибок</th><th>Создано</th></tr></thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>{run.id}</td><td>{t(run.mode)}</td><td>{t(run.status)}</td><td>{t(run.trigger_type)}</td><td>{run.scanned_pairs}</td><td>{run.allowed_total}</td><td>{run.executed_total}</td><td>{run.errors_total}</td><td>{formatDateTime(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Системные события">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Уровень</th><th>Источник</th><th>Тип</th><th>Сообщение</th><th>Создано</th></tr></thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{event.id}</td><td>{t(event.level)}</td><td>{event.source}</td><td>{t(event.event_type)}</td><td>{event.message}</td><td>{formatDateTime(event.created_at)}</td>
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
