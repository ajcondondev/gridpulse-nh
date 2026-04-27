import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { DownloadButton } from '../components/DownloadButton'
import { PageHeader } from '../components/PageHeader'
import { createJoin, getLatestJoin, joinDownloadUrl } from '../services/analysisApi'
import { getDatasetPreview } from '../services/datasetsApi'
import type { Dataset } from '../types/dataset'
import type { JoinedRow } from '../types/analysis'

export function WeatherDemandPage() {
  const [join, setJoin] = useState<Dataset | null>(null)
  const [chartData, setChartData] = useState<JoinedRow[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadPreview(dataset: Dataset) {
    try {
      const preview = await getDatasetPreview(dataset.id, 100)
      setChartData(preview.rows as unknown as JoinedRow[])
    } catch {
      // chart just stays empty
    }
  }

  useEffect(() => {
    getLatestJoin()
      .then(async (ds) => {
        setJoin(ds)
        await loadPreview(ds)
      })
      .catch((err: Error) => {
        if (!err.message.includes('404')) setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [])

  async function handleGenerate() {
    setGenerating(true)
    setError(null)
    try {
      const ds = await createJoin()
      setJoin(ds)
      await loadPreview(ds)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setGenerating(false)
    }
  }

  const hasData = chartData.length > 0

  return (
    <div data-testid="weather-demand-page">
      <PageHeader
        title="Weather &amp; Demand Analysis"
        subtitle="Daily electricity peak demand vs. temperature for New Hampshire."
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-800">
        <p className="font-medium mb-1">How weather drives electricity demand</p>
        <p className="text-blue-700 text-xs leading-relaxed">
          Electricity demand in New England tracks temperature closely. Cold days drive heating
          load (HDD), hot days drive cooling load (CDD). Utilities use this relationship to
          forecast peak demand and plan grid capacity. This analysis joins daily peak demand with
          average temperature for the most recently fetched datasets.
        </p>
        <p className="text-blue-500 text-xs mt-2 italic">
          Not official utility data. Public data relevant to New Hampshire analysis.
        </p>
      </div>

      {loading && <p className="text-gray-500 text-sm">Loading analysis...</p>}

      {!loading && !join && !error && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 text-sm mb-1">No analysis generated yet.</p>
          <p className="text-gray-400 text-xs mb-4">
            Fetch Mock Electricity Demand first, then generate the analysis here.
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 transition-colors disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Analysis'}
          </button>
        </div>
      )}

      {error && (
        <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          {error}
        </p>
      )}

      {join && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div>
              <p className="text-sm font-medium text-gray-900">{join.name}</p>
              <p className="text-xs text-gray-400 mt-0.5">
                {join.row_count} days &middot; generated{' '}
                {join.fetched_at ? new Date(join.fetched_at).toLocaleString() : ''}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="px-3 py-1.5 bg-white border border-gray-200 text-gray-600 rounded-lg text-xs font-medium hover:border-blue-400 transition-colors disabled:opacity-50"
              >
                {generating ? 'Regenerating...' : 'Regenerate'}
              </button>
              <DownloadButton href={joinDownloadUrl(join.id)} label="Download CSV" />
            </div>
          </div>

          {hasData ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
                Daily Peak Demand vs. Temperature
              </h2>
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 32, left: 8, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    tickFormatter={(v: string) => v.slice(5)}
                  />
                  <YAxis
                    yAxisId="mw"
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    label={{
                      value: 'Peak MW',
                      angle: -90,
                      position: 'insideLeft',
                      style: { fontSize: 10, fill: '#6b7280' },
                      offset: 8,
                    }}
                  />
                  <YAxis
                    yAxisId="temp"
                    orientation="right"
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    label={{
                      value: '°F',
                      angle: 90,
                      position: 'insideRight',
                      style: { fontSize: 10, fill: '#6b7280' },
                      offset: 8,
                    }}
                  />
                  <Tooltip
                    contentStyle={{ fontSize: 12 }}
                    formatter={(value: number, name: string) =>
                      name === 'Peak Demand (MW)'
                        ? [`${value.toFixed(1)} MW`, name]
                        : [`${value.toFixed(1)} °F`, name]
                    }
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line
                    yAxisId="mw"
                    type="monotone"
                    dataKey="daily_peak_mw"
                    name="Peak Demand (MW)"
                    stroke="#1d4ed8"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                  <Line
                    yAxisId="temp"
                    type="monotone"
                    dataKey="temp_avg_f"
                    name="Avg Temp (°F)"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                    strokeDasharray="5 3"
                  />
                </ComposedChart>
              </ResponsiveContainer>
              <p className="text-xs text-gray-400 mt-3 text-center">
                {chartData[0]?.weather_source === 'Mock Weather'
                  ? 'Temperature is synthetic mock data — not real NOAA observations. Fetch NOAA Weather for real data.'
                  : 'Temperature from NOAA GHCND — Manchester-Boston Regional Airport station.'}
              </p>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4 text-center text-sm text-gray-500">
              No chart data available.
            </div>
          )}

          {hasData && (
            <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
              <table className="min-w-full text-xs divide-y divide-gray-100">
                <thead className="bg-gray-50">
                  <tr>
                    {['date', 'region', 'daily_peak_mw', 'temp_avg_f', 'hdd', 'cdd', 'demand_source', 'weather_source'].map(
                      (col) => (
                        <th
                          key={col}
                          className="px-3 py-2 text-left font-semibold text-gray-500 uppercase tracking-wide font-mono whitespace-nowrap"
                        >
                          {col}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 bg-white">
                  {chartData.map((row, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono text-gray-700">{row.date}</td>
                      <td className="px-3 py-2 text-gray-600">{row.region ?? '—'}</td>
                      <td className="px-3 py-2 font-mono text-blue-700">{row.daily_peak_mw?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-2 font-mono text-red-700">{row.temp_avg_f?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-2 font-mono text-gray-600">{row.hdd?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-2 font-mono text-gray-600">{row.cdd?.toFixed(1) ?? '—'}</td>
                      <td className="px-3 py-2 text-gray-500">{row.demand_source ?? '—'}</td>
                      <td className="px-3 py-2 text-gray-500">{row.weather_source ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
