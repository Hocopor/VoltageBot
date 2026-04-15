import { NavLink, Route, Routes } from 'react-router-dom'
import AnalyticsPage from './pages/AnalyticsPage'
import BacktestsPage from './pages/BacktestsPage'
import BotPage from './pages/BotPage'
import DashboardPage from './pages/DashboardPage'
import JournalPage from './pages/JournalPage'
import IntegrationsPage from './pages/IntegrationsPage'
import OperationsPage from './pages/OperationsPage'
import OrdersPage from './pages/OrdersPage'
import PairsPage from './pages/PairsPage'
import SettingsPage from './pages/SettingsPage'
import StrategyPage from './pages/StrategyPage'
import ReleasePage from './pages/ReleasePage'

const navItems = [
  ['/', 'Dashboard'],
  ['/pairs', 'Pairs'],
  ['/orders', 'Orders'],
  ['/strategy', 'Strategy'],
  ['/backtests', 'Backtests'],
  ['/bot', 'Bot'],
  ['/operations', 'Operations'],
  ['/journal', 'Journal'],
  ['/analytics', 'Analytics'],
  ['/integrations', 'Integrations'],
  ['/release', 'Release'],
  ['/settings', 'Settings'],
]

export default function App() {
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
