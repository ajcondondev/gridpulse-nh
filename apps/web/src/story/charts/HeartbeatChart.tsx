import * as Plot from '@observablehq/plot'
import { useEffect } from 'react'
import demandHourlyJson from '@data/demand_hourly.json'
import { GRID_HAIRLINE, INK_MUTED, useContainerWidth } from '../chartTheme'

interface DemandHour {
  ts_utc: string
  demand_mw: number
}

const hours = (demandHourlyJson as DemandHour[]).map((d) => ({
  ts: new Date(d.ts_utc),
  demand_mw: d.demand_mw,
}))

const ACCENT = '#2a78d6'

export function HeartbeatChart() {
  const { ref, width } = useContainerWidth()

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const chart = Plot.plot({
      width,
      height: Math.max(240, Math.min(320, width * 0.34)),
      marginLeft: 48,
      marginBottom: 36,
      insetTop: 8,
      style: { fontSize: '12px', background: 'transparent', color: INK_MUTED },
      x: { label: null, tickSize: 0 },
      y: {
        label: 'Demand (MW)',
        tickFormat: (d: number) => `${(d / 1000).toFixed(0)}k`,
        tickSize: 0,
        nice: true,
        zero: false,
      },
      marks: [
        Plot.gridY({ stroke: GRID_HAIRLINE, strokeOpacity: 1 }),
        Plot.areaY(hours, {
          x: 'ts',
          y1: (d: (typeof hours)[number]) => d.demand_mw,
          y2: () => Math.min(...hours.map((h) => h.demand_mw)),
          fill: ACCENT,
          fillOpacity: 0.08,
        }),
        Plot.lineY(hours, {
          x: 'ts',
          y: 'demand_mw',
          stroke: ACCENT,
          strokeWidth: 1.75,
        }),
        Plot.tip(
          hours,
          Plot.pointerX({
            x: 'ts',
            y: 'demand_mw',
            title: (d: (typeof hours)[number]) =>
              `${d.ts.toLocaleString('en-US', {
                timeZone: 'America/New_York',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
              })}\n${d.demand_mw.toLocaleString()} MW`,
          }),
        ),
      ],
    })
    el.append(chart)
    return () => chart.remove()
  }, [ref, width])

  return (
    <div
      ref={ref}
      role="img"
      aria-label="Line chart of hourly ISO New England electricity demand over the most recent 30 days, showing a repeating daily rhythm: two peaks each day and lower demand overnight and on weekends."
      data-testid="heartbeat-chart"
    />
  )
}
