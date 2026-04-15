import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { PairSelections, SymbolItem } from '../types'

function toggleValue(list: string[], symbol: string) {
  return list.includes(symbol) ? list.filter((item) => item !== symbol) : [...list, symbol]
}

export default function PairsPage() {
  const [spotPairs, setSpotPairs] = useState<SymbolItem[]>([])
  const [futuresPairs, setFuturesPairs] = useState<SymbolItem[]>([])
  const [selections, setSelections] = useState<PairSelections>({ spot_symbols: [], futures_symbols: [] })
  const [message, setMessage] = useState('')

  useEffect(() => {
    api.getSpotPairs().then(setSpotPairs)
    api.getFuturesPairs().then(setFuturesPairs)
    api.getSelections().then(setSelections)
  }, [])

  const save = async () => {
    const result = await api.saveSelections(selections)
    setSelections(result)
    setMessage('Selections saved')
  }

  return (
    <Page title="Trading pairs" subtitle="Separate symbol selection for spot and futures USDT markets.">
      <div className="card-grid two-columns">
        <Card title="Spot symbols">
          <div className="list-box">
            {spotPairs.slice(0, 40).map((item) => (
              <label key={item.symbol} className="checkbox-row">
                <input type="checkbox" checked={selections.spot_symbols.includes(item.symbol)} onChange={() => setSelections((prev) => ({ ...prev, spot_symbols: toggleValue(prev.spot_symbols, item.symbol) }))} />
                <span>{item.symbol}</span>
              </label>
            ))}
          </div>
        </Card>
        <Card title="Futures symbols">
          <div className="list-box">
            {futuresPairs.slice(0, 40).map((item) => (
              <label key={item.symbol} className="checkbox-row">
                <input type="checkbox" checked={selections.futures_symbols.includes(item.symbol)} onChange={() => setSelections((prev) => ({ ...prev, futures_symbols: toggleValue(prev.futures_symbols, item.symbol) }))} />
                <span>{item.symbol}</span>
              </label>
            ))}
          </div>
        </Card>
      </div>
      <div className="action-row">
        <button onClick={save}>Save selections</button>
        {message ? <span className="message">{message}</span> : null}
      </div>
    </Page>
  )
}
