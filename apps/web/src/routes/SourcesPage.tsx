import { useEffect, useState } from 'react'
import { PageHeader } from '../components/PageHeader'
import { SourceCard } from '../components/SourceCard'
import { getSources } from '../services/sourcesApi'
import type { Source, SourceCategory } from '../types/source'

const CATEGORIES: Array<SourceCategory | 'all'> = [
  'all',
  'electricity',
  'weather',
  'ev',
  'environmental',
  'resilience',
  'gis',
  'regulatory',
]

const categoryLabel: Record<string, string> = {
  all: 'All',
  electricity: 'Electricity',
  weather: 'Weather',
  ev: 'EV',
  environmental: 'Environmental',
  resilience: 'Resilience',
  gis: 'GIS',
  regulatory: 'Regulatory',
}

export function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<SourceCategory | 'all'>('all')

  useEffect(() => {
    getSources()
      .then((data) => setSources(data.sources))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? sources : sources.filter((s) => s.category === filter)

  return (
    <div data-testid="sources-page">
      <PageHeader
        title="Data Sources"
        subtitle="Public utility data sources available for New Hampshire analysis."
      />

      <div className="flex flex-wrap gap-2 mb-6">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              filter === cat
                ? 'bg-blue-700 text-white border-blue-700'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-400 hover:text-blue-700'
            }`}
          >
            {categoryLabel[cat]}
          </button>
        ))}
      </div>

      {loading && <p className="text-gray-500 text-sm">Loading sources...</p>}
      {error && (
        <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
          Could not load sources: {error}
        </p>
      )}

      {!loading && !error && (
        <>
          <p className="text-xs text-gray-400 mb-4">
            Showing {filtered.length} of {sources.length} sources
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
