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
    setMessage('Выбранные пары сохранены.')
  }

  return (
    <Page title="Торговые пары" subtitle="Отдельный выбор инструментов для спота и фьючерсов на USDT.">
      <div className="card-grid two-columns">
        <Card title="Спот-пары">
          <div className="list-box">
            {spotPairs.map((item) => (
              <label key={item.symbol} className="checkbox-row">
                <input type="checkbox" checked={selections.spot_symbols.includes(item.symbol)} onChange={() => setSelections((prev) => ({ ...prev, spot_symbols: toggleValue(prev.spot_symbols, item.symbol) }))} />
                <span>{item.symbol}</span>
              </label>
            ))}
          </div>
        </Card>
        <Card title="Фьючерсные пары">
          <div className="list-box">
            {futuresPairs.map((item) => (
              <label key={item.symbol} className="checkbox-row">
                <input type="checkbox" checked={selections.futures_symbols.includes(item.symbol)} onChange={() => setSelections((prev) => ({ ...prev, futures_symbols: toggleValue(prev.futures_symbols, item.symbol) }))} />
                <span>{item.symbol}</span>
              </label>
            ))}
          </div>
        </Card>
      </div>
      <div className="action-row">
        <button onClick={save}>Сохранить выбор</button>
        {message ? <span className="message">{message}</span> : null}
      </div>
    </Page>
  )
}
