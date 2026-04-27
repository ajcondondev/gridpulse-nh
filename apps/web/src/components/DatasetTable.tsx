import { Link } from 'react-router-dom'
import type { Dataset } from '../types/dataset'

interface Props {
  datasets: Dataset[]
}

export function DatasetTable({ datasets }: Props) {
  if (datasets.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-sm text-gray-500">
        No datasets yet. Fetch a source to generate datasets.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200" data-testid="dataset-table">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Rows
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Fetched
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {datasets.map((ds) => (
            <tr key={ds.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium">
                <Link to={`/datasets/${ds.id}`} className="text-blue-700 hover:underline">
                  {ds.name}
                </Link>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    ds.status === 'ready'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {ds.status}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-600">{ds.row_count ?? '—'}</td>
              <td className="px-4 py-3 text-gray-500">
                {ds.fetched_at ? new Date(ds.fetched_at).toLocaleString() : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
