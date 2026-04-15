import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import type { AnalyticsReview, CodexBrowserStart, CodexStatus, DeepSeekStatus, DeepSeekTestResult, JournalEntry, StrategyDecision, StrategyExplanation } from '../types'

export default function IntegrationsPage() {
  const [codex, setCodex] = useState<CodexStatus | null>(null)
  const [pending, setPending] = useState<CodexBrowserStart | null>(null)
  const [accountLabel, setAccountLabel] = useState('browser-linked-user')
  const [deepseek, setDeepseek] = useState<DeepSeekStatus | null>(null)
  const [deepseekPrompt, setDeepseekPrompt] = useState('Сделай короткий health-check ответ для VOLTAGE.')
  const [deepseekResult, setDeepseekResult] = useState<DeepSeekTestResult | null>(null)
  const [decisions, setDecisions] = useState<StrategyDecision[]>([])
  const [decisionExplanation, setDecisionExplanation] = useState<StrategyExplanation | null>(null)
  const [analyticsReview, setAnalyticsReview] = useState<AnalyticsReview | null>(null)
  const [reviewedEntries, setReviewedEntries] = useState<JournalEntry[]>([])
  const [message, setMessage] = useState('')

  const load = async () => {
    const [codexStatus, deepseekStatus, strategyDecisions] = await Promise.all([
      api.getCodexStatus(),
      api.getDeepSeekStatus(),
      api.getStrategyDecisions(),
    ])
    setCodex(codexStatus)
    setDeepseek(deepseekStatus)
    setDecisions(strategyDecisions)
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof Error ? error.message : String(error)))
  }, [])

  const startLogin = async () => {
    try {
      const login = await api.startCodexBrowserLogin()
      setPending(login)
      setMessage(`Codex browser login started: ${login.login_id}`)
      setCodex(await api.getCodexStatus())
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const completeLogin = async () => {
    try {
      const loginId = pending?.login_id ?? codex?.pending_login_id
      if (!loginId) throw new Error('No pending login_id found')
      const status = await api.completeCodexBrowserLogin({ login_id: loginId, account_label: accountLabel })
      setCodex(status)
      setPending(null)
      setMessage('Codex browser session persisted')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const disconnect = async () => {
    try {
      const status = await api.disconnectCodex()
      setCodex(status)
      setPending(null)
      setMessage('Codex session removed')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const testDeepSeek = async () => {
    try {
      const result = await api.testDeepSeek(deepseekPrompt)
      setDeepseekResult(result)
      setMessage(`DeepSeek test status: ${result.status}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const explainLatestDecision = async () => {
    try {
      if (!decisions.length) throw new Error('No strategy decisions yet')
      const result = await api.explainStrategyDecision(decisions[0].id)
      setDecisionExplanation(result)
      setMessage(`Decision ${result.decision_id} explained`) 
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const reviewPending = async () => {
    try {
      const items = await api.reviewPendingJournal(5)
      setReviewedEntries(items)
      setMessage(`Reviewed ${items.length} journal entries`) 
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const summarizeAnalytics = async () => {
    try {
      const summary = await api.reviewAnalytics()
      setAnalyticsReview(summary)
      setMessage(`Analytics summary status: ${summary.status}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Integrations & AI" subtitle="Codex browser-session persistence, DeepSeek connectivity checks and AI assistance tools.">
      <div className="card-grid two-columns">
        <Card title="Codex browser login">
          <p>Status: <strong>{codex?.connected ? 'connected' : 'not connected'}</strong></p>
          <p>{codex?.message ?? 'No session yet.'}</p>
          {codex?.session_id ? <p>Session ID: <code>{codex.session_id}</code></p> : null}
          {codex?.account_label ? <p>Account: {codex.account_label}</p> : null}
          {codex?.connected_at ? <p>Connected at: {codex.connected_at}</p> : null}
          {codex?.pending_login ? <p>Pending login: <code>{codex.pending_login_id}</code></p> : null}
          <label className="field">
            <span>Account label</span>
            <input value={accountLabel} onChange={(e) => setAccountLabel(e.target.value)} />
          </label>
          <div className="action-row wrap">
            <button onClick={startLogin}>Start browser login</button>
            <button onClick={completeLogin}>Complete pending login</button>
            <button onClick={disconnect}>Disconnect</button>
          </div>
          {pending ? <p className="message-block">Callback path: {pending.callback_path}</p> : null}
        </Card>
        <Card title="DeepSeek status">
          <p>Configured: <strong>{deepseek?.configured ? 'yes' : 'no'}</strong></p>
          <p>{deepseek?.message ?? 'Loading status...'}</p>
          <p>Model: {deepseek?.model ?? '-'}</p>
          <label className="field">
            <span>Test prompt</span>
            <textarea rows={5} value={deepseekPrompt} onChange={(e) => setDeepseekPrompt(e.target.value)} />
          </label>
          <div className="action-row wrap">
            <button onClick={testDeepSeek}>Run DeepSeek test</button>
          </div>
          {deepseekResult ? <p className="message-block">[{deepseekResult.status}] {deepseekResult.text}</p> : null}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Strategy explainability">
          <p>Recent decisions: {decisions.length}</p>
          <div className="action-row wrap">
            <button onClick={explainLatestDecision}>Explain latest decision</button>
          </div>
          {decisionExplanation ? <p className="message-block">[{decisionExplanation.status}] {decisionExplanation.explanation}</p> : <p>No explanation generated yet.</p>}
        </Card>
        <Card title="Journal AI review queue">
          <div className="action-row wrap">
            <button onClick={reviewPending}>Review pending entries</button>
          </div>
          {reviewedEntries.length ? (
            <ul>
              {reviewedEntries.map((entry) => (
                <li key={entry.id}>#{entry.id} {entry.symbol} · {entry.ai_review_status}</li>
              ))}
            </ul>
          ) : <p>No reviewed entries in this session yet.</p>}
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="Analytics AI summary">
          <div className="action-row wrap">
            <button onClick={summarizeAnalytics}>Summarize analytics</button>
          </div>
          {analyticsReview ? <p className="message-block">[{analyticsReview.status}] {analyticsReview.text}</p> : <p>No analytics summary yet.</p>}
        </Card>
      </div>
      {message ? <p className="message-block">{message}</p> : null}
    </Page>
  )
}
