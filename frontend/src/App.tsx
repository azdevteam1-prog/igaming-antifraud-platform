import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import LiveDeposits from './pages/LiveDeposits'
import LiveWithdrawals from './pages/LiveWithdrawals'
import RulesStudio from './pages/RulesStudio'
import Players from './pages/Players'
import PlayerProfile from './pages/PlayerProfile'
import AlertsPage from './pages/AlertsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="deposits" element={<LiveDeposits />} />
        <Route path="withdrawals" element={<LiveWithdrawals />} />
        <Route path="rules" element={<RulesStudio />} />
        <Route path="players" element={<Players />} />
        <Route path="players/:id" element={<PlayerProfile />} />
        <Route path="alerts" element={<AlertsPage />} />
      </Route>
    </Routes>
  )
}
