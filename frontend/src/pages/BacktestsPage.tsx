import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
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
      setMessage(`Backtest #${created.id} completed`)
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
    <Page title="Historical backtests" subtitle="Run VOLTAGE on historical candles with separate historical balance and metrics.">
      <div className="card-grid two-columns">
        <Card title="Run backtest">
          <label className="field"><span>Market</span><select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures' })}><option value="spot">spot</option><option value="futures">futures</option></select></label>
          <label className="field"><span>Symbol</span><select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>{(availableSymbols.length ? availableSymbols : ['BTCUSDT']).map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}</select></label>
          <label className="field"><span>Timeframe</span><select value={form.timeframe} onChange={(e) => setForm({ ...form, timeframe: e.target.value })}><option value="15M">15M</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option></select></label>
          <label className="field"><span>Candles</span><input type="number" value={form.candles} onChange={(e) => setForm({ ...form, candles: Number(e.target.value) })} /></label>
          <label className="field"><span>Start balance</span><input type="number" value={form.start_balance} onChange={(e) => setForm({ ...form, start_balance: Number(e.target.value) })} /></label>
          <label className="field"><span>Side policy</span><select value={form.side_policy} onChange={(e) => setForm({ ...form, side_policy: e.target.value as 'both' | 'long_only' | 'short_only' })}><option value="both">both</option><option value="long_only">long_only</option><option value="short_only">short_only</option></select></label>
          <div className="action-row"><button onClick={run}>Run backtest</button></div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Selected run">
          {!selectedRun ? <p>No run selected.</p> : (
            <>
              <p><strong>#{selectedRun.id} {selectedRun.symbol}</strong> · {selectedRun.market_type}</p>
              <p>Trades {selectedRun.closed_trades} · Win rate {selectedRun.win_rate.toFixed(2)}%</p>
              <p>PnL {selectedRun.realized_pnl.toFixed(4)} · PF {selectedRun.profit_factor.toFixed(4)} · Avg RR {selectedRun.average_rr.toFixed(4)}</p>
              <p>Max drawdown {selectedRun.max_drawdown.toFixed(2)}% · Target metrics {selectedRun.target_metrics_met ? 'met' : 'not met'}</p>
              <p>{selectedRun.notes}</p>
            </>
          )}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Backtest runs">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Symbol</th><th>Trades</th><th>Win rate</th><th>PnL</th><th></th></tr>
              </thead>
              <tbody>
                {runs.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.symbol}</td>
                    <td>{item.closed_trades}</td>
                    <td>{item.win_rate.toFixed(2)}%</td>
                    <td>{item.realized_pnl.toFixed(4)}</td>
                    <td><button onClick={() => openRun(item.id)}>Open</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Run trades">
          {!selectedRun ? <p>Select a run.</p> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>ID</th><th>Dir</th><th>Entry idx</th><th>Exit idx</th><th>Entry</th><th>Exit</th><th>PnL</th><th>RR</th><th>Reason</th></tr>
                </thead>
                <tbody>
                  {selectedRun.trades.map((trade) => (
                    <tr key={trade.id}>
                      <td>{trade.id}</td>
                      <td>{trade.direction}</td>
                      <td>{trade.entry_index}</td>
                      <td>{trade.exit_index}</td>
                      <td>{trade.entry_price.toFixed(4)}</td>
                      <td>{trade.exit_price.toFixed(4)}</td>
                      <td>{trade.realized_pnl.toFixed(4)}</td>
                      <td>{trade.rr_multiple.toFixed(2)}</td>
                      <td>{trade.close_reason}</td>
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
