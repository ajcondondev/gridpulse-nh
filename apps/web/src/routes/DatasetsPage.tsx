import { useEffect, useState } from 'react'
import { DatasetTable } from '../components/DatasetTable'
import { PageHeader } from '../components/PageHeader'
import { getDatasets } from '../services/datasetsApi'
import type { Dataset } from '../types/dataset'

export function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDatasets()
      .then((data) => setDatasets(data.datasets))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div data-testid="datasets-page">
      <PageHeader
        title="Datasets"
        subtitle="Fetched and cleaned datasets ready for preview and download."
      />

      {loading && <p className="text-gray-500 text-sm">Loading datasets...</p>}
      {error && (
        <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3">
          Could not load datasets: {error}
        </p>
      )}

      {!loading && !error && (
        <>
          {datasets.length > 0 && (
            <p className="text-xs text-gray-400 mb-3">{datasets.length} dataset(s) available</p>
          )}
          <DatasetTable datasets={datasets} />
        </>
      )}
    </div>
  )
}
