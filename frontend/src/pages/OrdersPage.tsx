import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { ExecutionRequest, LiveLifecycleSyncResult, PositionLifecycleEvent, TradeOrder, TradePosition, TradeRecord } from '../types'

const defaultForm: ExecutionRequest = {
  symbol: 'BTCUSDT',
  market_type: 'spot',
  side: 'buy',
  order_type: 'market',
  risk_percent: 0.01,
}

const defaultLiveSync: LiveLifecycleSyncResult = {
  orders_checked: 0,
  orders_updated: 0,
  orders_filled: 0,
  orders_cancelled: 0,
  positions_seen: 0,
  positions_adopted: 0,
  positions_closed: 0,
  protections_applied: 0,
  created_events: 0,
  summary: 'No live lifecycle sync yet.',
}

export default function OrdersPage() {
  const [form, setForm] = useState<ExecutionRequest>(defaultForm)
  const [orders, setOrders] = useState<TradeOrder[]>([])
  const [trades, setTrades] = useState<TradeRecord[]>([])
  const [positions, setPositions] = useState<TradePosition[]>([])
  const [events, setEvents] = useState<PositionLifecycleEvent[]>([])
  const [message, setMessage] = useState('')
  const [liveSync, setLiveSync] = useState<LiveLifecycleSyncResult>(defaultLiveSync)

  const load = async () => {
    const [o, t, p, e] = await Promise.all([api.getOrders(), api.getTrades(), api.getPositions(), api.getLifecycleEvents()])
    setOrders(o)
    setTrades(t)
    setPositions(p)
    setEvents(e.slice(0, 20))
  }

  useEffect(() => {
    load().catch((error) => setMessage(String(error)))
  }, [])

  const activeSymbols = useMemo(() => positions.filter((item) => item.status === 'open').map((item) => item.symbol), [positions])

  const submit = async () => {
    try {
      const response = await api.executeTrade(form)
      setMessage(`Trade request accepted: ${JSON.stringify(response)}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncPaper = async () => {
    try {
      const response = await api.syncPaper()
      setMessage(`Paper sync: filled=${response.filled_orders}, closed=${response.closed_positions}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncLive = async () => {
    try {
      await api.syncLive()
      setMessage('Live account snapshot completed')
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncLiveLifecycle = async () => {
    try {
      const response = await api.syncLiveLifecycle()
      setLiveSync(response)
      setMessage(`Live lifecycle sync: ${response.summary}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncLifecycle = async () => {
    try {
      const response = await api.syncLifecycle()
      setMessage(`Lifecycle sync: synced=${response.synced_positions}, closed=${response.closed_positions}, events=${response.created_events}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const closePosition = async (id: number) => {
    try {
      const response = await api.closePosition(id)
      setMessage(`Position ${id} close action: ${JSON.stringify(response)}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Orders and positions" subtitle="Execution core, live lifecycle management and runtime monitoring for paper and live positions.">
      <div className="card-grid two-columns">
        <Card title="Execution form">
          {message ? <p className="message-block">{message}</p> : null}
          <label>Symbol</label>
          <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })} />
          <label>Market</label>
          <select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures', side: e.target.value === 'spot' ? 'buy' : form.side })}>
            <option value="spot">spot</option>
            <option value="futures">futures</option>
          </select>
          <label>Side</label>
          <select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as 'buy' | 'sell' })} disabled={form.market_type === 'spot'}>
            <option value="buy">buy</option>
            <option value="sell">sell</option>
          </select>
          <label>Order type</label>
          <select value={form.order_type} onChange={(e) => setForm({ ...form, order_type: e.target.value as 'market' | 'limit' })}>
            <option value="market">market</option>
            <option value="limit">limit</option>
          </select>
          <label>Qty</label>
          <input type="number" value={form.qty ?? ''} onChange={(e) => setForm({ ...form, qty: e.target.value ? Number(e.target.value) : undefined })} />
          <label>Risk %</label>
          <input type="number" step="0.01" min="0.01" max="0.03" value={form.risk_percent} onChange={(e) => setForm({ ...form, risk_percent: Number(e.target.value) })} />
          <div className="actions-row">
            <button onClick={submit}>Execute</button>
            <button onClick={syncPaper}>Sync paper market</button>
            <button onClick={syncLive}>Snapshot live</button>
          </div>
          <div className="actions-row" style={{ marginTop: 8 }}>
            <button onClick={syncLiveLifecycle}>Sync live lifecycle</button>
            <button onClick={syncLifecycle}>Sync paper lifecycle</button>
          </div>
          <p>Active symbols: {activeSymbols.length ? activeSymbols.join(', ') : 'none'}</p>
        </Card>
        <Card title="Live lifecycle sync summary">
          <p>Orders checked: <strong>{liveSync.orders_checked}</strong></p>
          <p>Orders updated: {liveSync.orders_updated}</p>
          <p>Orders filled: {liveSync.orders_filled}</p>
          <p>Orders cancelled: {liveSync.orders_cancelled}</p>
          <p>Positions seen: {liveSync.positions_seen}</p>
          <p>Positions adopted: {liveSync.positions_adopted}</p>
          <p>Positions closed: {liveSync.positions_closed}</p>
          <p>Protections applied: {liveSync.protections_applied}</p>
          <p>{liveSync.summary}</p>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Open positions">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Mode</th><th>Symbol</th><th>Side</th><th>Status</th><th>Entry</th><th>Mark</th><th>Ext size</th><th>Pos idx</th><th></th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.id}>
                    <td>{position.id}</td>
                    <td>{position.mode}</td>
                    <td>{position.symbol}</td>
                    <td>{position.side}</td>
                    <td>{position.status}</td>
                    <td>{position.avg_entry_price.toFixed(4)}</td>
                    <td>{position.mark_price?.toFixed(4) ?? '-'}</td>
                    <td>{position.last_exchange_size?.toFixed(4) ?? '-'}</td>
                    <td>{position.position_idx ?? 0}</td>
                    <td>{position.status === 'open' ? <button onClick={() => closePosition(position.id)}>Close</button> : null}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Orders">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Mode</th><th>Symbol</th><th>Stage</th><th>Status</th><th>Exch.</th><th>Reduce</th><th>Qty</th></tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.id}</td><td>{order.mode}</td><td>{order.symbol}</td><td>{order.stage}</td><td>{order.status}</td><td>{order.last_exchange_status ?? '-'}</td><td>{order.reduce_only ? 'yes' : 'no'}</td><td>{order.qty.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Trades">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Mode</th><th>Symbol</th><th>Direction</th><th>Status</th><th>Realized</th><th>Unrealized</th></tr>
              </thead>
              <tbody>
                {trades.map((trade) => (
                  <tr key={trade.id}>
                    <td>{trade.id}</td><td>{trade.mode}</td><td>{trade.symbol}</td><td>{trade.direction}</td><td>{trade.status}</td><td>{trade.realized_pnl.toFixed(4)}</td><td>{trade.unrealized_pnl.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Lifecycle events">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ID</th><th>Symbol</th><th>Type</th><th>Message</th><th>Price</th><th>Created</th></tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{event.id}</td><td>{event.symbol}</td><td>{event.event_type}</td><td>{event.message}</td><td>{event.price?.toFixed(4) ?? '-'}</td><td>{event.created_at}</td>
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
