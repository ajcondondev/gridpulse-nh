import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { getSources } from '../services/sourcesApi'
import type { Source } from '../types/source'

export function Dashboard() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSources()
      .then((data) => setSources(data.sources))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const total = sources.length
  const available = sources.filter((s) => s.status === 'active').length
  const planned = sources.filter((s) => s.status === 'planned').length

  return (
    <div data-testid="dashboard-page">
      <PageHeader
        title="Dashboard"
        subtitle="Overview of public utility data sources for New Hampshire."
      />

      {loading && <p className="text-gray-500 text-sm">Loading sources...</p>}
      {error && (
        <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
          Could not load sources: {error}
        </p>
      )}

      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <StatCard label="Total Sources" value={total} />
            <StatCard label="Available Now" value={available} />
            <StatCard label="Planned" value={planned} />
          </div>

          <h2 className="text-base font-semibold text-gray-900 mb-3">Sources</h2>
          <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
            {sources.slice(0, 6).map((source) => (
              <Link
                key={source.id}
                to={`/sources/${source.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="min-w-0 flex-1 pr-4">
                  <p className="text-sm font-medium text-gray-900">{source.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{source.description}</p>
                </div>
                <StatusBadge status={source.status} />
              </Link>
            ))}
          </div>

          <div className="mt-3 text-right">
            <Link to="/sources" className="text-sm text-blue-700 hover:underline">
              View all {total} sources &rarr;
            </Link>
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}
