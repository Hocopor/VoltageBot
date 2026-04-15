import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
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
      setMessage(`Review generated for entry ${entryId}`)
      await load()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Trader journal" subtitle="Live, paper and historical entries with enriched lifecycle metrics and AI post-trade review.">
      <div className="card-grid four-columns">
        <Card title="Entries"><strong>{summary.total_entries}</strong></Card>
        <Card title="Realized PnL"><strong>{summary.total_realized_pnl.toFixed(4)}</strong></Card>
        <Card title="Wins / losses"><strong>{summary.wins} / {summary.losses}</strong></Card>
        <Card title="Avg hold"><strong>{summary.avg_hold_minutes.toFixed(2)}m</strong></Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Journal entries">
          {message ? <p className="message-block">{message}</p> : null}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Mode</th><th>Symbol</th><th>Direction</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Reason</th><th>Hold</th><th>Best</th><th>Worst</th><th>Compliance</th><th>AI review</th><th></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.id}</td>
                    <td>{entry.mode}</td>
                    <td>{entry.symbol}</td>
                    <td>{entry.direction}</td>
                    <td>{entry.entry_price.toFixed(4)}</td>
                    <td>{entry.exit_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.realized_pnl.toFixed(4)}</td>
                    <td>{entry.close_reason ?? '-'}</td>
                    <td>{entry.hold_minutes?.toFixed(2) ?? '-'}</td>
                    <td>{entry.best_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.worst_price?.toFixed(4) ?? '-'}</td>
                    <td>{entry.compliance_score?.toFixed(2) ?? '-'}</td>
                    <td>{entry.ai_review_text ?? entry.ai_review_status}</td>
                    <td><button onClick={() => review(entry.id)}>Review</button></td>
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
