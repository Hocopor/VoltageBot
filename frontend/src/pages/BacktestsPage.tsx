import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { t } from '../format'
import type { BacktestRun, BacktestRunDetail, BacktestRunRequest, PairSelections } from '../types'

const initialForm: BacktestRunRequest = {
  symbol: 'BTCUSDT',
  market_type: 'spot',
  timeframe: '1H',
  candles: 240,
  start_balance: 10000,
  side_policy: 'both',
}

export default function BacktestsPage() {
  const [form, setForm] = useState<BacktestRunRequest>(initialForm)
  const [runs, setRuns] = useState<BacktestRun[]>([])
  const [selectedRun, setSelectedRun] = useState<BacktestRunDetail | null>(null)
  const [selections, setSelections] = useState<PairSelections>({ spot_symbols: [], futures_symbols: [] })
  const [message, setMessage] = useState('')

  const load = async () => {
    const [runList, selected] = await Promise.all([api.getBacktestRuns(), api.getSelections()])
    setRuns(runList)
    setSelections(selected)
  }

  useEffect(() => {
    load().catch((error) => setMessage(String(error)))
  }, [])

  const availableSymbols = form.market_type === 'spot' ? selections.spot_symbols : selections.futures_symbols

  const run = async () => {
    try {
      const created = await api.runBacktest(form)
      setMessage(`Бэктест #${created.id} завершён.`)
      await load()
      setSelectedRun(await api.getBacktestRun(created.id))
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const openRun = async (runId: number) => {
    setSelectedRun(await api.getBacktestRun(runId))
  }

  return (
    <Page title="Исторические бэктесты" subtitle="Прогоняйте VOLTAGE на исторических свечах с отдельным балансом и статистикой.">
      <div className="card-grid two-columns">
        <Card title="Запуск бэктеста">
          <label className="field"><span>Рынок</span><select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures' })}><option value="spot">Спот</option><option value="futures">Фьючерсы</option></select></label>
          <label className="field"><span>Инструмент</span><select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>{(availableSymbols.length ? availableSymbols : ['BTCUSDT']).map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}</select></label>
          <label className="field"><span>Таймфрейм</span><select value={form.timeframe} onChange={(e) => setForm({ ...form, timeframe: e.target.value })}><option value="15M">15M</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option></select></label>
          <label className="field"><span>Свечей</span><input type="number" value={form.candles} onChange={(e) => setForm({ ...form, candles: Number(e.target.value) })} /></label>
          <label className="field"><span>Стартовый баланс</span><input type="number" value={form.start_balance} onChange={(e) => setForm({ ...form, start_balance: Number(e.target.value) })} /></label>
          <label className="field"><span>Политика направлений</span><select value={form.side_policy} onChange={(e) => setForm({ ...form, side_policy: e.target.value as 'both' | 'long_only' | 'short_only' })}><option value="both">Обе стороны</option><option value="long_only">Только лонг</option><option value="short_only">Только шорт</option></select></label>
          <div className="action-row"><button onClick={run}>Запустить бэктест</button></div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Выбранный прогон">
          {!selectedRun ? <p>Прогон не выбран.</p> : (
            <>
              <p><strong>#{selectedRun.id} {selectedRun.symbol}</strong> · {t(selectedRun.market_type)}</p>
              <p>Сделок: {selectedRun.closed_trades} · Win rate: {selectedRun.win_rate.toFixed(2)}%</p>
              <p>PnL: {selectedRun.realized_pnl.toFixed(4)} · PF: {selectedRun.profit_factor.toFixed(4)} · Ср. R/R: {selectedRun.average_rr.toFixed(4)}</p>
              <p>Макс. просадка: {selectedRun.max_drawdown.toFixed(2)}% · Целевые метрики: {selectedRun.target_metrics_met ? 'выполнены' : 'не выполнены'}</p>
              <p>{selectedRun.notes}</p>
            </>
          )}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Прогоны бэктеста">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Инструмент</th><th>Сделок</th><th>Win rate</th><th>PnL</th><th></th></tr>
              </thead>
              <tbody>
                {runs.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.symbol}</td>
                    <td>{item.closed_trades}</td>
                    <td>{item.win_rate.toFixed(2)}%</td>
                    <td>{item.realized_pnl.toFixed(4)}</td>
                    <td><button onClick={() => openRun(item.id)}>Открыть</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Сделки прогона">
          {!selectedRun ? <p>Выберите прогон.</p> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>ID</th><th>Напр.</th><th>Индекс входа</th><th>Индекс выхода</th><th>Вход</th><th>Выход</th><th>PnL</th><th>R/R</th><th>Причина</th></tr>
                </thead>
                <tbody>
                  {selectedRun.trades.map((trade) => (
                    <tr key={trade.id}>
                      <td>{trade.id}</td>
                      <td>{t(trade.direction)}</td>
                      <td>{trade.entry_index}</td>
                      <td>{trade.exit_index}</td>
                      <td>{trade.entry_price.toFixed(4)}</td>
                      <td>{trade.exit_price.toFixed(4)}</td>
                      <td>{trade.realized_pnl.toFixed(4)}</td>
                      <td>{trade.rr_multiple.toFixed(2)}</td>
                      <td>{t(trade.close_reason)}</td>
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
