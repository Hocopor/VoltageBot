import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { t } from '../format'
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
      setMessage(`Решение ${data.created_decision_id} сохранено.`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Стратегия" subtitle="Проверка фильтров VOLTAGE на текущих или резервных исторических свечах.">
      <div className="card-grid two-columns">
        <Card title="Оценка сигнала">
          <label className="field">
            <span>Рынок</span>
            <select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures', side: e.target.value === 'spot' ? 'buy' : form.side })}>
              <option value="spot">Спот</option>
              <option value="futures">Фьючерсы</option>
            </select>
          </label>
          <label className="field">
            <span>Инструмент</span>
            <select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
              {(availableSymbols.length ? availableSymbols : ['BTCUSDT']).map((symbol) => <option key={symbol} value={symbol}>{symbol}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Направление</span>
            <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as 'buy' | 'sell' })}>
              <option value="buy">Лонг / Покупка</option>
              {form.market_type === 'futures' ? <option value="sell">Шорт / Продажа</option> : null}
            </select>
          </label>
          <label className="field">
            <span>Таймфрейм</span>
            <select value={form.timeframe} onChange={(e) => setForm({ ...form, timeframe: e.target.value })}>
              <option value="15M">15M</option>
              <option value="1H">1H</option>
              <option value="4H">4H</option>
              <option value="1D">1D</option>
            </select>
          </label>
          <label className="field">
            <span>Свечей</span>
            <input type="number" value={form.candles} onChange={(e) => setForm({ ...form, candles: Number(e.target.value) })} />
          </label>
          <div className="action-row">
            <button onClick={evaluate}>Оценить стратегию</button>
          </div>
          {message ? <p className="message-block">{message}</p> : null}
        </Card>
        <Card title="Последний результат">
          {!result ? <p>Оценка ещё не выполнялась.</p> : (
            <>
              <p><strong>{result.allowed ? 'Разрешено' : 'Заблокировано'}</strong> · сценарий {t(result.market_scenario)} · confidence {result.confidence.toFixed(2)}</p>
              <p>Вход: {result.entry_price.toFixed(4)}</p>
              <p>Стоп-лосс: {result.stop_loss.toFixed(4)}</p>
              <p>TP1 {result.take_profit_1.toFixed(4)} · TP2 {result.take_profit_2.toFixed(4)} · TP3 {result.take_profit_3.toFixed(4)}</p>
              <p>{result.filter_summary}</p>
              <p>{result.risk_summary}</p>
            </>
          )}
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Журнал решений">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Инструмент</th><th>Разрешено</th><th>Сценарий</th><th>Уверенность</th><th>Сводка</th></tr>
              </thead>
              <tbody>
                {decisions.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.symbol}</td>
                    <td>{item.allowed ? 'да' : 'нет'}</td>
                    <td>{t(item.market_scenario)}</td>
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
