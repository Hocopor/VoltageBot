import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import type { AuthSession } from './types'
import { api } from './api'
import AnalyticsPage from './pages/AnalyticsPage'
import BacktestsPage from './pages/BacktestsPage'
import BotPage from './pages/BotPage'
import DashboardPage from './pages/DashboardPage'
import JournalPage from './pages/JournalPage'
import IntegrationsPage from './pages/IntegrationsPage'
import LoginPage from './pages/LoginPage'
import OperationsPage from './pages/OperationsPage'
import OrdersPage from './pages/OrdersPage'
import PairsPage from './pages/PairsPage'
import SettingsPage from './pages/SettingsPage'
import StrategyPage from './pages/StrategyPage'
import ReleasePage from './pages/ReleasePage'

const navItems = [
  ['/', 'Панель'],
  ['/pairs', 'Пары'],
  ['/orders', 'Ордера'],
  ['/strategy', 'Стратегия'],
  ['/backtests', 'Бэктест'],
  ['/bot', 'Бот'],
  ['/operations', 'Операции'],
  ['/journal', 'Дневник'],
  ['/analytics', 'Аналитика'],
  ['/integrations', 'Интеграции'],
  ['/release', 'Релиз'],
  ['/settings', 'Настройки'],
]

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [loading, setLoading] = useState(true)

  const loadSession = async () => {
    try {
      setSession(await api.getSession())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSession()
    const handler = () => setSession({ authenticated: false, message: 'Требуется вход.' })
    window.addEventListener('voltage:auth-required', handler)
    return () => window.removeEventListener('voltage:auth-required', handler)
  }, [])

  useEffect(() => {
    if (session?.authenticated) {
      document.title = 'VOLTAGE'
    }
  }, [session])

  const logout = async () => {
    await api.logout()
    setSession({ authenticated: false, message: 'Вы вышли из системы.' })
  }

  if (loading) {
    return <div className="login-shell"><div className="login-panel login-loading" /></div>
  }

  if (!session?.authenticated) {
    return <LoginPage onSuccess={setSession} />
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">VOLTAGE</div>
        <nav>
          {navItems.map(([href, label]) => (
            <NavLink key={href} to={href} end={href === '/'} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">{session.username}</div>
          <button className="secondary-button" onClick={logout}>Выйти</button>
        </div>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/pairs" element={<PairsPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/strategy" element={<StrategyPage />} />
          <Route path="/backtests" element={<BacktestsPage />} />
          <Route path="/bot" element={<BotPage />} />
          <Route path="/operations" element={<OperationsPage />} />
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/release" element={<ReleasePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
