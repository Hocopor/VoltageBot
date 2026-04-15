import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, Page } from '../components'
import { formatDateTime, t, yesNo } from '../format'
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
      setMessage(`Запущен браузерный вход Codex: ${login.login_id}`)
      setCodex(await api.getCodexStatus())
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const completeLogin = async () => {
    try {
      const loginId = pending?.login_id ?? codex?.pending_login_id
      if (!loginId) throw new Error('Не найден pending login_id.')
      const status = await api.completeCodexBrowserLogin({ login_id: loginId, account_label: accountLabel })
      setCodex(status)
      setPending(null)
      setMessage('Сессия Codex сохранена локально.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const disconnect = async () => {
    try {
      const status = await api.disconnectCodex()
      setCodex(status)
      setPending(null)
      setMessage('Сессия Codex удалена.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const testDeepSeek = async () => {
    try {
      const result = await api.testDeepSeek(deepseekPrompt)
      setDeepseekResult(result)
      setMessage(`Проверка DeepSeek: ${t(result.status)}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const explainLatestDecision = async () => {
    try {
      if (!decisions.length) throw new Error('Решений стратегии пока нет.')
      const result = await api.explainStrategyDecision(decisions[0].id)
      setDecisionExplanation(result)
      setMessage(`Решение ${result.decision_id} разобрано.`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const reviewPending = async () => {
    try {
      const items = await api.reviewPendingJournal(5)
      setReviewedEntries(items)
      setMessage(`Разобрано записей дневника: ${items.length}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  const summarizeAnalytics = async () => {
    try {
      const summary = await api.reviewAnalytics()
      setAnalyticsReview(summary)
      setMessage(`Сводка аналитики: ${t(summary.status)}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <Page title="Интеграции и AI" subtitle="Сессия Codex, проверка подключения DeepSeek и инструменты AI-разбора.">
      <div className="card-grid two-columns">
        <Card title="Вход Codex через браузер">
          <p>Статус: <strong>{codex?.connected ? 'подключено' : 'не подключено'}</strong></p>
          <p>{codex?.message ?? 'Сессии пока нет.'}</p>
          {codex?.session_id ? <p>ID сессии: <code>{codex.session_id}</code></p> : null}
          {codex?.account_label ? <p>Аккаунт: {codex.account_label}</p> : null}
          {codex?.connected_at ? <p>Подключено: {formatDateTime(codex.connected_at)}</p> : null}
          {codex?.pending_login ? <p>Ожидает вход: <code>{codex.pending_login_id}</code></p> : null}
          <label className="field">
            <span>Метка аккаунта</span>
            <input value={accountLabel} onChange={(e) => setAccountLabel(e.target.value)} />
          </label>
          <div className="action-row wrap">
            <button onClick={startLogin}>Начать вход через браузер</button>
            <button onClick={completeLogin}>Завершить ожидающий вход</button>
            <button onClick={disconnect}>Отключить</button>
          </div>
          {pending ? <p className="message-block">Путь callback: {pending.callback_path}</p> : null}
        </Card>
        <Card title="Статус DeepSeek">
          <p>Настроен: <strong>{yesNo(deepseek?.configured)}</strong></p>
          <p>{deepseek?.message ?? 'Загрузка статуса...'}</p>
          <p>Модель: {deepseek?.model ?? '-'}</p>
          <label className="field">
            <span>Тестовый запрос</span>
            <textarea rows={5} value={deepseekPrompt} onChange={(e) => setDeepseekPrompt(e.target.value)} />
          </label>
          <div className="action-row wrap">
            <button onClick={testDeepSeek}>Запустить проверку DeepSeek</button>
          </div>
          {deepseekResult ? <p className="message-block">[{t(deepseekResult.status)}] {deepseekResult.text}</p> : null}
        </Card>
      </div>
      <div className="card-grid two-columns">
        <Card title="Объяснение решений стратегии">
          <p>Последних решений: {decisions.length}</p>
          <div className="action-row wrap">
            <button onClick={explainLatestDecision}>Разобрать последнее решение</button>
          </div>
          {decisionExplanation ? <p className="message-block">[{t(decisionExplanation.status)}] {decisionExplanation.explanation}</p> : <p>Объяснение пока не формировалось.</p>}
        </Card>
        <Card title="Очередь AI-разбора дневника">
          <div className="action-row wrap">
            <button onClick={reviewPending}>Разобрать ожидающие записи</button>
          </div>
          {reviewedEntries.length ? (
            <ul>
              {reviewedEntries.map((entry) => (
                <li key={entry.id}>#{entry.id} {entry.symbol} · {t(entry.ai_review_status)}</li>
              ))}
            </ul>
          ) : <p>В этой сессии ещё ничего не разбиралось.</p>}
        </Card>
      </div>
      <div className="card-grid single-column">
        <Card title="AI-сводка аналитики">
          <div className="action-row wrap">
            <button onClick={summarizeAnalytics}>Сформировать AI-сводку</button>
          </div>
          {analyticsReview ? <p className="message-block">[{t(analyticsReview.status)}] {analyticsReview.text}</p> : <p>Сводка аналитики пока не создавалась.</p>}
        </Card>
      </div>
      {message ? <p className="message-block">{message}</p> : null}
    </Page>
  )
}
