import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, t } from '../format'
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
  summary: 'Синхронизация live lifecycle ещё не выполнялась.',
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
    const [o, tList, p, e] = await Promise.all([api.getOrders(), api.getTrades(), api.getPositions(), api.getLifecycleEvents()])
    setOrders(o)
    setTrades(tList)
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
      setMessage(`Торговый запрос принят: ${JSON.stringify(response)}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncPaper = async () => {
    try {
      const response = await api.syncPaper()
      setMessage(`Paper sync: исполнено ${response.filled_orders}, закрыто ${response.closed_positions}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const syncLive = async () => {
    try {
      await api.syncLive()
      setMessage('Снимок live-аккаунта выполнен.')
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
      setMessage(`Lifecycle sync: синхронизировано ${response.synced_positions}, закрыто ${response.closed_positions}, событий ${response.created_events}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const closePosition = async (id: number) => {
    try {
      const response = await api.closePosition(id)
      setMessage(`Команда на закрытие позиции ${id}: ${JSON.stringify(response)}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Ордера и позиции" subtitle="Торговое ядро, сопровождение lifecycle и мониторинг paper/live-позиций.">
      <div className="card-grid two-columns">
        <Card title="Форма исполнения">
          {message ? <p className="message-block">{message}</p> : null}
          <label className="field"><span>Инструмент</span><input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })} /></label>
          <label className="field"><span>Рынок</span><select value={form.market_type} onChange={(e) => setForm({ ...form, market_type: e.target.value as 'spot' | 'futures', side: e.target.value === 'spot' ? 'buy' : form.side })}><option value="spot">Спот</option><option value="futures">Фьючерсы</option></select></label>
          <label className="field"><span>Направление</span><select value={form.side} onChange={(e) => setForm({ ...form, side: e.target.value as 'buy' | 'sell' })} disabled={form.market_type === 'spot'}><option value="buy">Лонг / Покупка</option><option value="sell">Шорт / Продажа</option></select></label>
          <label className="field"><span>Тип ордера</span><select value={form.order_type} onChange={(e) => setForm({ ...form, order_type: e.target.value as 'market' | 'limit' })}><option value="market">Маркет</option><option value="limit">Лимит</option></select></label>
          <label className="field"><span>Количество</span><input type="number" value={form.qty ?? ''} onChange={(e) => setForm({ ...form, qty: e.target.value ? Number(e.target.value) : undefined })} /></label>
          <label className="field"><span>Риск, %</span><input type="number" step="0.01" min="0.01" max="0.03" value={form.risk_percent} onChange={(e) => setForm({ ...form, risk_percent: Number(e.target.value) })} /></label>
          <div className="action-row">
            <button onClick={submit}>Исполнить</button>
            <button onClick={syncPaper}>Синхронизировать paper</button>
            <button onClick={syncLive}>Снимок live</button>
          </div>
          <div className="action-row">
            <button onClick={syncLiveLifecycle}>Sync live lifecycle</button>
            <button onClick={syncLifecycle}>Sync paper lifecycle</button>
          </div>
          <p>Активные инструменты: {activeSymbols.length ? activeSymbols.join(', ') : 'нет'}</p>
        </Card>
        <Card title="Сводка live lifecycle sync">
          <p>Проверено ордеров: <strong>{liveSync.orders_checked}</strong></p>
          <p>Обновлено ордеров: {liveSync.orders_updated}</p>
          <p>Исполнено ордеров: {liveSync.orders_filled}</p>
          <p>Отменено ордеров: {liveSync.orders_cancelled}</p>
          <p>Обнаружено позиций: {liveSync.positions_seen}</p>
          <p>Подхвачено позиций: {liveSync.positions_adopted}</p>
          <p>Закрыто позиций: {liveSync.positions_closed}</p>
          <p>Защит применено: {liveSync.protections_applied}</p>
          <p>{liveSync.summary}</p>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Позиции">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Режим</th><th>Инструмент</th><th>Направление</th><th>Статус</th><th>Вход</th><th>Марк</th><th>Размер на бирже</th><th>Pos idx</th><th></th></tr></thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.id}>
                    <td>{position.id}</td><td>{t(position.mode)}</td><td>{position.symbol}</td><td>{t(position.side)}</td><td>{t(position.status)}</td><td>{position.avg_entry_price.toFixed(4)}</td><td>{position.mark_price?.toFixed(4) ?? '-'}</td><td>{position.last_exchange_size?.toFixed(4) ?? '-'}</td><td>{position.position_idx ?? 0}</td><td>{position.status === 'open' ? <button onClick={() => closePosition(position.id)}>Закрыть</button> : null}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Ордера">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Режим</th><th>Инструмент</th><th>Этап</th><th>Статус</th><th>Статус биржи</th><th>Reduce only</th><th>Кол-во</th></tr></thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.id}</td><td>{t(order.mode)}</td><td>{order.symbol}</td><td>{t(order.stage)}</td><td>{t(order.status)}</td><td>{t(order.last_exchange_status)}</td><td>{order.reduce_only ? 'да' : 'нет'}</td><td>{order.qty.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Сделки">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Режим</th><th>Инструмент</th><th>Направление</th><th>Статус</th><th>Реализовано</th><th>Нереализовано</th></tr></thead>
              <tbody>
                {trades.map((trade) => (
                  <tr key={trade.id}>
                    <td>{trade.id}</td><td>{t(trade.mode)}</td><td>{trade.symbol}</td><td>{t(trade.direction)}</td><td>{t(trade.status)}</td><td>{trade.realized_pnl.toFixed(4)}</td><td>{trade.unrealized_pnl.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="События lifecycle">
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Инструмент</th><th>Тип</th><th>Сообщение</th><th>Цена</th><th>Создано</th></tr></thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{event.id}</td><td>{event.symbol}</td><td>{t(event.event_type)}</td><td>{event.message}</td><td>{event.price?.toFixed(4) ?? '-'}</td><td>{formatDateTime(event.created_at)}</td>
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
