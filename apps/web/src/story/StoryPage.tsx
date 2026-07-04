import { Link } from 'react-router-dom'
import { meta, tempDemandDaily } from '../lib/processedData'
import { ChartCard } from './ChartCard'
import { VCurveChart } from './charts/VCurveChart'

function computeStats() {
  const sorted = [...tempDemandDaily].sort((a, b) => b.peak_mw - a.peak_mw)
  const top = sorted[0]
  const mild = tempDemandDaily.filter((d) => d.temp_avg_f >= 55 && d.temp_avg_f <= 65)
  const mildAvgPeak = mild.length
    ? mild.reduce((sum, d) => sum + d.peak_mw, 0) / mild.length
    : 0
  return { top, mildAvgPeak }
}

export function StoryPage() {
  const { top, mildAvgPeak } = computeStats()
  const ratio = mildAvgPeak ? (top.peak_mw / mildAvgPeak).toFixed(1) : null
  const generated = new Date(meta.generated_at)

  return (
    <div data-testid="story-page" className="max-w-4xl mx-auto">
      {/* Hero */}
      <header className="pt-6 pb-10 sm:pt-12 sm:pb-14">
        <p className="text-xs font-semibold uppercase tracking-widest text-blue-700 mb-3">
          A public-data story · New England&apos;s grid
        </p>
        <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
          Weather runs the grid.
        </h1>
        <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
          Every day, New England&apos;s electricity demand follows the thermometer. Using{' '}
          {meta.coverage.days.toLocaleString()} days of public hourly data from the U.S. Energy
          Information Administration and weather history for Concord,&nbsp;NH, this project traces
          how temperature drives demand — and what happens when the weather turns extreme.
        </p>
        <p className="mt-4 text-xs text-slate-400">
          Data: {meta.coverage.start} → {meta.coverage.end} · refreshed{' '}
          {generated.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}{' '}
          · <Link to="/explorer" className="underline hover:text-slate-600">explore the raw data</Link>
        </p>
      </header>

      {/* Act 1: the V-curve */}
      <section className="space-y-6 pb-16">
        <div className="max-w-2xl">
          <h2 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight">
            Demand has a shape — and it&apos;s a V
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 leading-relaxed">
            On mild days the region idles along at its base load. Push the temperature down and
            heating load climbs; push it up and air conditioning takes over. The result is one of
            the most reliable curves in the energy world.
            {ratio && top && (
              <>
                {' '}
                The single biggest day in this dataset —{' '}
                <span className="font-medium text-slate-800">
                  {top.peak_mw.toLocaleString()} MW on {top.date} ({top.temp_avg_f}°F average)
                </span>{' '}
                — ran about {ratio}× the typical mild-day peak.
              </>
            )}
          </p>
        </div>

        <ChartCard
          title="Hot or cold, New England reaches for the switch"
          subtitle={`Each dot is one day (${meta.coverage.start} → ${meta.coverage.end}): daily average temperature in Concord, NH vs. ISO New England peak demand. The dark line is the average peak per 2°F band.`}
          source="EIA-930 Hourly Electric Grid Monitor (ISNE); Open-Meteo / ERA5 hourly temperature, Concord NH"
          caveat="Preliminary EIA-930 values; one weather point is a proxy for regional weather. Educational project — not affiliated with ISO-NE or any utility."
        >
          <VCurveChart />
        </ChartCard>
      </section>

      {/* What's next teaser (removed as sections ship) */}
      <section className="pb-16">
        <div className="border border-dashed border-slate-300 rounded-xl p-6 text-sm text-slate-500 leading-relaxed">
          <p className="font-medium text-slate-600 mb-1">More of the story is on the way</p>
          <p>
            Next: the grid&apos;s daily heartbeat, a calendar of peak days, what fuels the region
            hour by hour, and an hour-by-hour replay of the June 2025 heat wave — when demand hit{' '}
            {top ? top.peak_mw.toLocaleString() : '25,898'} MW and oil-fired plants came off the
            bench.
          </p>
        </div>
      </section>
    </div>
  )
}

export default StoryPage
