import { Link, NavLink, Outlet } from 'react-router-dom'

const navLinks = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/sources', label: 'Sources', end: false },
  { to: '/datasets', label: 'Datasets', end: false },
  { to: '/analysis/weather-demand', label: 'Weather & Demand', end: false },
]

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-blue-900 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex flex-col leading-tight" data-testid="app-title">
            <span className="text-lg font-bold tracking-tight">GridPulse NH</span>
            <span className="text-xs text-blue-300">
              Public utility, weather, EV, and grid data in one workbench.
            </span>
          </Link>
          <nav className="flex gap-1" aria-label="Main navigation">
            {navLinks.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  `px-3 py-2 rounded text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-700 text-white'
                      : 'text-blue-100 hover:bg-blue-800 hover:text-white'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-gray-400 text-center">
          GridPulse NH &mdash; Not official Eversource software. Public data relevant to New
          Hampshire utility analysis.
        </div>
      </footer>
    </div>
  )
}
