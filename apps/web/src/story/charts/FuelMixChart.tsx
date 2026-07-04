import * as Plot from '@observablehq/plot'
import { useEffect } from 'react'
import fuelMixDailyJson from '@data/fuel_mix_daily.json'
import {
  FUEL_COLORS,
  FUEL_LABELS,
  FUEL_ORDER,
  GRID_HAIRLINE,
  INK_MUTED,
  useContainerWidth,
  type FuelKey,
} from '../chartTheme'

interface FuelDay {
  date: string
  fuel: string
  avg_mw: number
  share: number | null
}

/** Coal + storage + misc fold into "other"; storage charging (negative) is clipped for the area. */
function displayFuel(fuel: string): FuelKey {
  return (FUEL_ORDER as readonly string[]).includes(fuel) ? (fuel as FuelKey) : 'other'
}

const byDate = new Map<string, Map<FuelKey, number>>()
for (const row of fuelMixDailyJson as FuelDay[]) {
  const fuel = displayFuel(row.fuel)
  const day = byDate.get(row.date) ?? new Map<FuelKey, number>()
  day.set(fuel, (day.get(fuel) ?? 0) + Math.max(0, row.avg_mw))
  byDate.set(row.date, day)
}
const series = [...byDate.entries()].flatMap(([date, fuels]) =>
  FUEL_ORDER.filter((f) => fuels.has(f)).map((fuel) => ({
    date: new Date(`${date}T12:00:00`),
    fuel,
    avg_mw: fuels.get(fuel) ?? 0,
  })),
)

export function FuelMixChart() {
  const { ref, width } = useContainerWidth()

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const chart = Plot.plot({
      width,
      height: Math.max(300, Math.min(400, width * 0.42)),
      marginLeft: 48,
      marginBottom: 36,
      style: { fontSize: '12px', background: 'transparent', color: INK_MUTED },
      x: { label: null, tickSize: 0 },
      y: {
        label: 'Average generation (MW)',
        tickFormat: (d: number) => `${(d / 1000).toFixed(0)}k`,
        tickSize: 0,
      },
      color: {
        domain: [...FUEL_ORDER],
        range: FUEL_ORDER.map((f) => FUEL_COLORS[f]),
        tickFormat: (f: FuelKey) => FUEL_LABELS[f],
        legend: true,
      },
      marks: [
        Plot.gridY({ stroke: GRID_HAIRLINE, strokeOpacity: 1 }),
        Plot.areaY(series, {
          x: 'date',
          y: 'avg_mw',
          fill: 'fuel',
          order: [...FUEL_ORDER],
          tip: false,
        }),
        Plot.tip(
          series,
          Plot.pointerX(
            Plot.stackY({
              x: 'date',
              y: 'avg_mw',
              fill: 'fuel',
              order: [...FUEL_ORDER],
              title: (d: (typeof series)[number]) =>
                `${d.date.toISOString().slice(0, 10)}\n${FUEL_LABELS[d.fuel]}: ${Math.round(
                  d.avg_mw,
                ).toLocaleString()} MW`,
            }),
          ),
        ),
        Plot.ruleY([0], { stroke: INK_MUTED }),
      ],
    })
    el.append(chart)
    return () => chart.remove()
  }, [ref, width])

  return (
    <div
      ref={ref}
      role="img"
      aria-label="Stacked area chart of ISO New England daily average generation by fuel. Natural gas is the largest band throughout; nuclear is a steady base; solar and wind form thinner bands; oil appears as small spikes during extreme weather."
      data-testid="fuel-mix-chart"
    />
  )
}
