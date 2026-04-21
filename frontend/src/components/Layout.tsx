import { Outlet, NavLink } from 'react-router-dom'
import { Shield, TrendingDown, TrendingUp, BookOpen, Users, Bell, LayoutDashboard } from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/deposits', icon: TrendingUp, label: 'Live Deposits' },
  { to: '/withdrawals', icon: TrendingDown, label: 'Live Withdrawals' },
  { to: '/rules', icon: BookOpen, label: 'Rules Studio' },
  { to: '/players', icon: Users, label: 'Players' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
]

export default function Layout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-800">
          <Shield className="text-indigo-400" size={24} />
          <span className="font-bold text-white text-sm">AntiFraud iGaming</span>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx('flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition',
                  isActive ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white')
              }
            >
              <Icon size={16} />{label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-gray-800 text-xs text-gray-500">
          v1.0.0 • Real-time mode
        </div>
      </aside>
      {/* Main */}
      <main className="flex-1 overflow-auto bg-gray-950">
        <Outlet />
      </main>
    </div>
  )
}
