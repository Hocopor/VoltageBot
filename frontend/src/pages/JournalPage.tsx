import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, t } from '../format'
import type { JournalEntry, JournalSummary } from '../types'

const emptySummary: JournalSummary = {
  total_entries: 0,
  total_realized_pnl: 0,
  wins: 0,
  losses: 0,
  avg_hold_minutes: 0,
  by_mode: {},
}

export default function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [summary, setSummary] = useState<JournalSummary>(emptySummary)
  const [message, setMessage] = useState('')

  const load = async () => {
    const [journal, info] = await Promise.all([api.getJournal(), api.getJournalSummary()])
    setEntries(journal)
    setSummary(info)
  }

  useEffect(() => {
    load().catch(() => setEntries([]))
  }, [])

  const review = async (entryId: number) => {
    try {
      await api.reviewJournalEntry(entryId)
      setMessage(`AI-разбор для записи ${entryId} сформирован.`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Дневник трейдера" subtitle="Сделки из live, paper и historical с расширенными метриками жизненного цикла и AI-разбором после закрытия.">
      <div className="card-grid four-columns">
        <Card title="Записи"><strong>{summary.total_entries}</strong></Card>
        <Card title="Реализованный PnL"><strong>{summary.total_realized_pnl.toFixed(4)}</strong></Card>
        <Card title="Прибыльные / убыточные"><strong>{summary.wins} / {summary.losses}</strong></Card>
        <Card title="Среднее удержание"><strong>{summary.avg_hold_minutes.toFixed(2)} мин</strong></Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Записи дневника">
          {message ? <p className="message-block">{message}</p> : null}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Режим</th><th>Инструмент</th><th>Направление</th><th>Вход</th><th>Выход</th><th>PnL</th><th>Причина</th><th>Удержание</th><th>Лучшая цена</th><th>Худшая цена</th><th>Соблюдение</th><th>AI-разбор</th><th>Создано</th><th></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.id}</td>
                    <td>{t(entry.mode)}</td>
                    <td>{entry.symbol}</td>
                    <td>{t(entry.direction)}</td>
                    <td>{entry.entry_price.toFixed(4)}</td>
                    <td>{entry.exit_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.realized_pnl.toFixed(4)}</td>
                    <td>{t(entry.close_reason)}</td>
                    <td>{entry.hold_minutes?.toFixed(2) ?? '-'}</td>
                    <td>{entry.best_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.worst_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.compliance_score?.toFixed(2) ?? '-'}</td>
                    <td>{entry.ai_review_text ?? t(entry.ai_review_status)}</td>
                    <td>{formatDateTime(entry.created_at)}</td>
                    <td><button onClick={() => review(entry.id)}>Разобрать</button></td>
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
