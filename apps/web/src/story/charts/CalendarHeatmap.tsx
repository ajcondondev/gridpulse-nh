import * as Plot from '@observablehq/plot'
import { useEffect } from 'react'
import demandDailyJson from '@data/demand_daily.json'
import { INK_MUTED, SEQ_BLUES, useContainerWidth } from '../chartTheme'

interface DemandDay {
  date: string
  peak_mw: number
  avg_mw: number
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const days = (demandDailyJson as DemandDay[]).map((d) => {
  const date = new Date(`${d.date}T12:00:00`)
  const year = date.getFullYear()
  const jan1 = new Date(year, 0, 1)
  const dayOfYear = Math.floor((date.getTime() - jan1.getTime()) / 86_400_000)
  // ISO-ish week column: weeks start Monday.
  const jan1Weekday = (jan1.getDay() + 6) % 7
  const week = Math.floor((dayOfYear + jan1Weekday) / 7)
  return {
    ...d,
    year,
    week,
    weekday: WEEKDAYS[(date.getDay() + 6) % 7],
    month: date.toLocaleString('en-US', { month: 'short' }),
  }
})

export function CalendarHeatmap() {
  const { ref, width } = useContainerWidth()

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const years = [...new Set(days.map((d) => d.year))].sort()
    const chart = Plot.plot({
      width,
      height: years.length * 128 + 48,
      marginLeft: 42,
      padding: 0.08,
      style: { fontSize: '11px', background: 'transparent', color: INK_MUTED },
      x: { axis: null },
      y: { domain: WEEKDAYS, label: null, tickSize: 0 },
      fy: { label: null },
      color: {
        type: 'quantile',
        n: 7,
        range: SEQ_BLUES,
        label: 'Daily peak (MW)',
        legend: true,
        tickFormat: (d: number) => `${(d / 1000).toFixed(0)}k`,
      },
      marks: [
        Plot.cell(days, {
          x: 'week',
          y: 'weekday',
          fy: 'year',
          fill: 'peak_mw',
          rx: 2,
          inset: 0.75,
          tip: true,
          title: (d: (typeof days)[number]) =>
            `${d.date}\npeak ${d.peak_mw.toLocaleString()} MW`,
        }),
        // Month initials along the top of each year band.
        Plot.text(
          days.filter((d) => new Date(`${d.date}T12:00:00`).getDate() === 1),
          {
            x: 'week',
            fy: 'year',
            text: 'month',
            frameAnchor: 'top',
            dy: -14,
            fill: INK_MUTED,
          },
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
      aria-label="Calendar heatmap of daily peak electricity demand. Dark cells cluster in January, February, and late June through July, showing that the highest-demand days come in winter cold and summer heat; spring and fall stay light."
      data-testid="calendar-heatmap"
    />
  )
}
