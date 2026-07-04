import { Link } from 'react-router-dom'
import eventWindowJson from '@data/event_window.json'
import { meta, tempDemandDaily } from '../lib/processedData'
import { ChartCard } from './ChartCard'
import { CalendarHeatmap } from './charts/CalendarHeatmap'
import { EventReplay } from './charts/EventReplay'
import { FuelMixChart } from './charts/FuelMixChart'
import { HeartbeatChart } from './charts/HeartbeatChart'
import { VCurveChart } from './charts/VCurveChart'

const eventInfo = eventWindowJson as unknown as {
  kind: string
  start_date: string
  end_date: string
}

function computeStats() {
  const sorted = [...tempDemandDaily].sort((a, b) => b.peak_mw - a.peak_mw)
  const top = sorted[0]
  const mild = tempDemandDaily.filter((d) => d.temp_avg_f >= 55 && d.temp_avg_f <= 65)
  const mildAvgPeak = mild.length
    ? mild.reduce((sum, d) => sum + d.peak_mw, 0) / mild.length
    : 0
  return { top, mildAvgPeak }
}

const SOURCE_LINE =
  'EIA-930 Hourly Electric Grid Monitor (ISNE); Open-Meteo / ERA5 hourly temperature, Concord NH'
const CAVEAT_LINE =
  'Preliminary EIA-930 values; one weather point is a proxy for regional weather. Educational project — not affiliated with ISO-NE or any utility.'

function SectionIntro({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="max-w-2xl">
      <h2 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight">
        {title}
      </h2>
      <p className="mt-2 text-sm sm:text-base text-slate-600 leading-relaxed">{children}</p>
    </div>
  )
}

export function StoryPage() {
  const { top, mildAvgPeak } = computeStats()
  const ratio = mildAvgPeak ? (top.peak_mw / mildAvgPeak).toFixed(1) : null
  const generated = new Date(meta.generated_at)
  const eventKindLabel = eventInfo.kind === 'cold_snap' ? 'cold snap' : 'heat wave'

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

      {/* Act 1: the heartbeat */}
      <section className="space-y-6 pb-16">
        <SectionIntro title="The grid has a heartbeat">
          Thirty days of hourly demand look like a pulse: two peaks a day — morning coffee and
          evening dinner — lower on weekends, rising and falling with the workweek. This rhythm is
          so regular that grid operators plan around it years in advance. The interesting part is
          what breaks it.
        </SectionIntro>
        <ChartCard
          title="Thirty days of the region's pulse"
          subtitle="Hourly ISO New England system demand, most recent 30 days in the dataset."
          source="EIA-930 Hourly Electric Grid Monitor (ISNE)"
          caveat={CAVEAT_LINE}
        >
          <HeartbeatChart />
        </ChartCard>
      </section>

      {/* Act 2: the V-curve */}
      <section className="space-y-6 pb-16">
        <SectionIntro title="Demand has a shape — and it's a V">
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
        </SectionIntro>
        <ChartCard
          title="Hot or cold, New England reaches for the switch"
          subtitle={`Each dot is one day (${meta.coverage.start} → ${meta.coverage.end}): daily average temperature in Concord, NH vs. ISO New England peak demand. The dark line is the average peak per 2°F band.`}
          source={SOURCE_LINE}
          caveat={CAVEAT_LINE}
        >
          <VCurveChart />
        </ChartCard>
      </section>

      {/* Act 3: a year of peaks */}
      <section className="space-y-6 pb-16">
        <SectionIntro title="A year of peaks, at a glance">
          Lay every day on a calendar and the seasons jump out: demand ridges in deep winter and
          high summer, valleys in spring and fall when nobody is heating or cooling. New
          England&apos;s hardest days cluster in exactly two kinds of weather.
        </SectionIntro>
        <ChartCard
          title="The hard days come in winter and summer"
          subtitle="Daily peak demand, one cell per day. Darker means a higher peak."
          source="EIA-930 Hourly Electric Grid Monitor (ISNE)"
          caveat={CAVEAT_LINE}
        >
          <CalendarHeatmap />
        </ChartCard>
      </section>

      {/* Act 4: the event replay */}
      <section className="space-y-6 pb-16">
        <SectionIntro title={`Replay: the ${eventKindLabel} that stressed the grid`}>
          From {eventInfo.start_date} to {eventInfo.end_date}, New England lived through the
          hardest stretch in this dataset. Press play — or drag the scrubber — to watch
          temperature, demand, and the generation mix react hour by hour. The cards below appear
          as the story unfolds; every number in them is computed from the data.
        </SectionIntro>
        <ChartCard
          title="One week, hour by hour"
          subtitle="Top to bottom: Concord temperature, ISO-NE system demand, and each fuel's share of generation."
          source={SOURCE_LINE}
          caveat={CAVEAT_LINE}
        >
          <EventReplay />
        </ChartCard>
      </section>

      {/* Act 5: what's burning */}
      <section className="space-y-6 pb-16">
        <SectionIntro title="What's actually generating">
          Behind every one of those megawatts is a fuel. Natural gas carries New England most
          hours; nuclear runs flat around the clock; solar bites into the middle of the day; and
          on the very hardest days, oil-fired plants — normally idle — come off the bench. That
          last band is the grid&apos;s stress indicator.
        </SectionIntro>
        <ChartCard
          title="A gas-powered region with a nuclear floor"
          subtitle="Daily average generation by fuel group. 'Other' folds in coal, storage, and miscellaneous sources."
          source="EIA-930 Hourly Electric Grid Monitor (ISNE)"
          caveat={CAVEAT_LINE}
        >
          <FuelMixChart />
        </ChartCard>
      </section>

      {/* Methodology footer */}
      <section className="pb-16">
        <div className="border border-slate-200 bg-white rounded-xl p-6 text-sm text-slate-600 leading-relaxed">
          <p className="font-semibold text-slate-800 mb-1">How this was made</p>
          <p>
            A Python pipeline pulls EIA-930 bulk files and ERA5 weather history, normalizes them
            into small tidy JSON artifacts, and commits them to the repo — so this page runs with
            no backend and no API keys. Charts are Observable Plot with a dash of D3 and Motion.
            Full details, caveats, and rebuild instructions are in the{' '}
            <a
              href="https://github.com/ajcondondev/gridpulse-nh/blob/master/docs/methodology.md"
              className="underline hover:text-slate-900"
              target="_blank"
              rel="noreferrer"
            >
              methodology notes
            </a>
            .
          </p>
        </div>
      </section>
    </div>
  )
}

export default StoryPage
