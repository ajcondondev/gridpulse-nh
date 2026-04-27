import { Link } from 'react-router-dom'
import type { Source } from '../types/source'
import { StatusBadge } from './StatusBadge'

const categoryLabel: Record<string, string> = {
  electricity: 'Electricity',
  weather: 'Weather',
  ev: 'EV / Transportation',
  environmental: 'Environmental',
  resilience: 'Resilience',
  gis: 'GIS',
  regulatory: 'Regulatory',
}

interface Props {
  source: Source
}

export function SourceCard({ source }: Props) {
  return (
    <Link
      to={`/sources/${source.id}`}
      className="block bg-white border border-gray-200 rounded-lg p-5 hover:border-blue-400 hover:shadow-sm transition-all"
      data-testid="source-card"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900 leading-snug">{source.name}</h3>
        <StatusBadge status={source.status} />
      </div>
      <p className="mt-1 text-xs font-medium text-blue-700">
        {categoryLabel[source.category] ?? source.category}
      </p>
      <p className="mt-2 text-sm text-gray-600 line-clamp-2">{source.description}</p>
      {source.update_frequency && (
        <p className="mt-3 text-xs text-gray-400">Updated: {source.update_frequency}</p>
      )}
    </Link>
  )
}
