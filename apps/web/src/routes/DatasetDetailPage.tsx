import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { DownloadButton } from '../components/DownloadButton'
import { PageHeader } from '../components/PageHeader'
import { cleanedDownloadUrl, getDataset, getDatasetPreview, rawDownloadUrl } from '../services/datasetsApi'
import type { Dataset, DatasetPreview } from '../types/dataset'

export function DatasetDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>()
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!datasetId) return
    Promise.all([getDataset(datasetId), getDatasetPreview(datasetId)])
      .then(([ds, pv]) => {
        setDataset(ds)
        setPreview(pv)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [datasetId])

  if (loading) return <p className="text-gray-500 text-sm">Loading dataset...</p>
  if (error)
    return (
      <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
        {error}
      </p>
    )
  if (!dataset || !datasetId) return <p className="text-gray-500 text-sm">Dataset not found.</p>

  return (
    <div data-testid="dataset-detail-page">
      <div className="mb-4">
        <Link to="/datasets" className="text-sm text-blue-700 hover:underline">
          &larr; Back to Datasets
        </Link>
      </div>

      <PageHeader title={dataset.name} />

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
          Dataset Info
        </h2>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <dt className="text-xs font-medium text-gray-500">Status</dt>
            <dd className="mt-0.5">
              <span
                className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                  dataset.status === 'ready'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {dataset.status}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Rows</dt>
            <dd className="mt-0.5 text-gray-900 font-semibold">{dataset.row_count ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Source</dt>
            <dd className="mt-0.5 text-gray-900">{dataset.source_id}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Fetched</dt>
            <dd className="mt-0.5 text-gray-900">
              {dataset.fetched_at ? new Date(dataset.fetched_at).toLocaleString() : '—'}
            </dd>
          </div>
          {dataset.columns && (
            <div className="col-span-2 sm:col-span-4">
              <dt className="text-xs font-medium text-gray-500">Columns</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {dataset.columns.map((col) => (
                  <span
                    key={col}
                    className="px-2 py-0.5 bg-blue-50 text-blue-800 text-xs rounded font-mono"
                  >
                    {col}
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
          Downloads
        </h2>
        <div className="flex flex-wrap gap-3">
          <DownloadButton href={cleanedDownloadUrl(datasetId)} label="Download Cleaned CSV" />
          <DownloadButton href={rawDownloadUrl(datasetId)} label="Download Raw CSV" />
        </div>
        {dataset.source_id === 'mock_demand' && (
          <p className="mt-2 text-xs text-gray-400">
            Synthetic mock data — clearly labeled. Not real utility data.
          </p>
        )}
        {dataset.source_id !== 'mock_demand' && (
          <p className="mt-2 text-xs text-gray-400">
            Public data relevant to New Hampshire utility analysis. Not official Eversource software.
          </p>
        )}
      </div>

      {preview && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Preview
            </h2>
            <p className="text-xs text-gray-400">
              Showing {preview.preview_row_count} of {preview.total_row_count ?? dataset.row_count}{' '}
              rows
            </p>
          </div>
          <div className="overflow-x-auto rounded-lg border border-gray-100">
            <table className="min-w-full text-xs divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  {preview.columns.map((col) => (
                    <th
                      key={col}
                      className="px-3 py-2 text-left font-semibold text-gray-500 uppercase tracking-wide font-mono whitespace-nowrap"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 bg-white">
                {preview.rows.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-gray-700 whitespace-nowrap font-mono">
                        {String(row[col] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
