import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api'
import type { AuthSession } from '../types'

export default function LoginPage({ onSuccess }: { onSuccess: (session: AuthSession) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    document.title = 'Вход'
  }, [])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      const session = await api.login({ username, password })
      onSuccess(session)
      setPassword('')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-shell">
      <form className="login-panel" onSubmit={submit}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Логин" autoComplete="username" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" type="password" autoComplete="current-password" />
        <button type="submit" disabled={submitting}>{submitting ? 'Вход...' : 'Войти'}</button>
        {message ? <div className="login-error">{message}</div> : null}
      </form>
    </div>
  )
}
