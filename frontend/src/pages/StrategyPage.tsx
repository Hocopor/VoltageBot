import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { PairSelections, StrategyDecision, StrategyEvaluationRequest, StrategyEvaluationResponse } from '../types'

const initialForm: StrategyEvaluationRequest = {
  symbol: 'BTCUSDT',
  market_type: 'spot',
  side: 'buy',
  timeframe: '1H',
  candles: 240,
}

export default function StrategyPage() {
  const [form, setForm] = useState<StrategyEvaluationRequest>(initialForm)
  const [selections, setSelections] = useState<PairSelections>({ spot_symbols: [], futures_symbols: [] })
  const [result, setResult] = useState<StrategyEvaluationResponse | null>(null)
  const [decisions, setDecisions] = useState<StrategyDecision[]>([])
  const [message, setMessage] = useState('')

  const load = async () => {
    const [selected, decisionList] = await Promise.all([api.getSelections(), api.getStrategyDecisions()])
    setSelections(selected)
    setDecisions(decisionList)
  }

  useEffect(() => {
    load().catch((error) => setMessage(String(error)))
  }, [])

  const availableSymbols = form.market_type === 'spot' ? selections.spot_symbols : selections.futures_symbols

  const evaluate = async () => {
    try {
      const data = await api.evaluateStrategy(form)
      setResult(data)
      setMessage(`Decision ${data.created_decision_id} saved`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Strategy engine" subtitle="Evaluate VOLTAGE filters against current or fallback historical candles.">
      <div className="card-grid two-columns">
        <Card title="Evaluate signal">
          <label className="field">
            <span>Market</span>
            <select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures', side: e.target.value === 'spot' ? 'buy' : form.side })}>
              <option value="spot">spot</option>
              <option value="futures">futures</option>
            </select>
          </label>
          <label className="field">
            <span>Symbol</span>
            <select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
              {(availableSymbols.length ? availableSymbols : ['BTCUSDT']).map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Side</span>
            <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as 'buy' | 'sell' })}>
              <option value="buy">buy</option>
              {form.market_type === 'futures' ? <option value="sell">sell</option> : null}
            </select>
          </label>
          <label className="field">
            <span>Timeframe</span>
            <select value={form.timeframe} onChange={(e) => setForm({ ...form, timeframe: e.target.value })}>
              <option value="15M">15M</option>
              <option value="1H">1H</option>
              <option value="4H">4H</option>
              <option value="1D">1D</option>
            </select>
          </label>
          <label className="field">
            <span>Candles</span>
            <input type="number" value={form.candles} onChange={(e) => setForm({ ...form, candles: Number(e.target.value) })} />
          </label>
          <div className="action-row">
            <button onClick={evaluate}>Evaluate strategy</button>
          </div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Latest result">
          {!result ? <p>No evaluation yet.</p> : (
            <>
              <p><strong>{result.allowed ? 'Allowed' : 'Blocked'}</strong> · scenario {result.market_scenario} · confidence {result.confidence.toFixed(2)}</p>
              <p>Entry {result.entry_price.toFixed(4)}</p>
              <p>SL {result.stop_loss.toFixed(4)}</p>
              <p>TP1 {result.take_profit_1.toFixed(4)} · TP2 {result.take_profit_2.toFixed(4)} · TP3 {result.take_profit_3.toFixed(4)}</p>
              <p>{result.filter_summary}</p>
              <p>{result.risk_summary}</p>
            </>
          )}
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Decision log">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Symbol</th><th>Allowed</th><th>Scenario</th><th>Confidence</th><th>Summary</th></tr>
              </thead>
              <tbody>
                {decisions.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.symbol}</td>
                    <td>{item.allowed ? 'yes' : 'no'}</td>
                    <td>{item.market_scenario ?? '-'}</td>
                    <td>{item.confidence.toFixed(2)}</td>
                    <td>{item.filter_summary ?? '-'}</td>
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
