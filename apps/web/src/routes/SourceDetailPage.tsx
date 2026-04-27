import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { fetchSource, getSource } from '../services/sourcesApi'
import type { Dataset } from '../types/dataset'
import type { Source } from '../types/source'

const ACCESS_METHOD_LABELS: Record<string, string> = {
  api: 'Live API (JSON)',
  arcgis_rest: 'ArcGIS REST API',
  csv_download: 'CSV Download',
  web_scrape: 'Web Scrape (HTML)',
  pdf: 'PDF / Document',
  manual: 'Manual Import',
  generated: 'Generated (synthetic)',
}

type FetchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; dataset: Dataset }
  | { status: 'error'; message: string }

export function SourceDetailPage() {
  const { sourceId } = useParams<{ sourceId: string }>()
  const [source, setSource] = useState<Source | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fetchState, setFetchState] = useState<FetchState>({ status: 'idle' })

  useEffect(() => {
    if (!sourceId) return
    getSource(sourceId)
      .then(setSource)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [sourceId])

  async function handleFetch() {
    if (!sourceId) return
    setFetchState({ status: 'loading' })
    try {
      const dataset = (await fetchSource(sourceId)) as Dataset
      setFetchState({ status: 'success', dataset })
    } catch (err) {
      setFetchState({ status: 'error', message: (err as Error).message })
    }
  }

  if (loading) return <p className="text-gray-500 text-sm">Loading...</p>
  if (error)
    return (
      <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
        {error}
      </p>
    )
  if (!source) return <p className="text-gray-500 text-sm">Source not found.</p>

  const FETCHABLE_IDS = new Set([
    'mock_demand',
    'eia_isone_load',
    'isone_csv',
    'noaa_weather',
    'afdc_ev',
    'openei_rates',
    'epa_egrid',
    'cdc_svi',
    'fema_flood',
    'nh_geodata',
  ])
  const canFetch = FETCHABLE_IDS.has(source.id)
  const noKeyRequired = !source.requires_api_key

  return (
    <div data-testid="source-detail-page">
      <div className="mb-4">
        <Link to="/sources" className="text-sm text-blue-700 hover:underline">
          &larr; Back to Sources
        </Link>
      </div>

      <div className="flex flex-wrap items-start gap-3 mb-6">
        <div className="flex-1">
          <PageHeader title={source.name} />
        </div>
        <div className="pt-1">
          <StatusBadge status={source.status} />
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
          About This Source
        </h2>
        <p className="text-sm text-gray-700 leading-relaxed">{source.description}</p>

        <dl className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-xs font-medium text-gray-500">Category</dt>
            <dd className="mt-0.5 text-gray-900 capitalize">{source.category}</dd>
          </div>
          {source.update_frequency && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Update Frequency</dt>
              <dd className="mt-0.5 text-gray-900">{source.update_frequency}</dd>
            </div>
          )}
          {source.data_format && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Data Format</dt>
              <dd className="mt-0.5 text-gray-900">{source.data_format}</dd>
            </div>
          )}
          {source.url && (
            <div className="sm:col-span-2">
              <dt className="text-xs font-medium text-gray-500">Source URL</dt>
              <dd className="mt-0.5">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 hover:underline break-all"
                >
                  {source.url}
                </a>
              </dd>
            </div>
          )}
          {source.access_method && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Access Method</dt>
              <dd className="mt-0.5 text-gray-900">{ACCESS_METHOD_LABELS[source.access_method] ?? source.access_method}</dd>
            </div>
          )}
          {source.requires_api_key != null && (
            <div>
              <dt className="text-xs font-medium text-gray-500">API Key Required</dt>
              <dd className="mt-0.5 text-gray-900">
                {source.requires_api_key
                  ? <span className="text-amber-700">Yes — see .env setup in README</span>
                  : <span className="text-emerald-700">No</span>}
              </dd>
            </div>
          )}
          {source.phase_added != null && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Phase Added</dt>
              <dd className="mt-0.5 text-gray-900">Phase {source.phase_added}</dd>
            </div>
          )}
          {source.last_verified && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Last Verified</dt>
              <dd className="mt-0.5 text-gray-900">{source.last_verified}</dd>
            </div>
          )}
          {source.notes && (
            <div className="sm:col-span-2">
              <dt className="text-xs font-medium text-gray-500">Notes</dt>
              <dd className="mt-0.5 text-gray-600">{source.notes}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
          Actions
        </h2>

        <button
          onClick={handleFetch}
          disabled={!canFetch || fetchState.status === 'loading'}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            canFetch && fetchState.status !== 'loading'
              ? 'bg-blue-700 text-white hover:bg-blue-800'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
          data-testid="fetch-button"
        >
          {fetchState.status === 'loading' ? 'Fetching...' : 'Fetch Latest Data'}
        </button>

        {!canFetch && (
          <p className="mt-2 text-xs text-gray-400">
            Will be enabled once the API connector is configured.
          </p>
        )}

        {fetchState.status === 'idle' && canFetch && source.status === 'mock' && (
          <p className="mt-2 text-xs text-gray-400">
            Generates synthetic mock data. Clearly labeled — not real utility data.
          </p>
        )}

        {fetchState.status === 'idle' && canFetch && source.status !== 'mock' && !noKeyRequired && (
          <p className="mt-2 text-xs text-gray-400">
            Requires an API key configured in the backend .env file. See README for setup.
          </p>
        )}

        {fetchState.status === 'idle' && canFetch && noKeyRequired && (
          <p className="mt-2 text-xs text-gray-400">
            Fetches from a live public source with no API key required.
          </p>
        )}

        {fetchState.status === 'success' && (
          <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm">
            <p className="font-medium text-emerald-800">Dataset ready</p>
            <p className="text-emerald-700 mt-0.5">
              {fetchState.dataset.name} &mdash; {fetchState.dataset.row_count} rows
            </p>
            <Link
              to={`/datasets/${fetchState.dataset.id}`}
              className="inline-block mt-2 text-blue-700 hover:underline text-xs font-medium"
            >
              View dataset &rarr;
            </Link>
          </div>
        )}

        {fetchState.status === 'error' && (
          <p className="mt-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {fetchState.message}
          </p>
        )}
      </div>
    </div>
  )
}
